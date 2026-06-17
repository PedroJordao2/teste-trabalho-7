import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config import ConfigError, load_network
from .network import ALGORITHMS, search
from .output import append_result_csv, print_result


DEFAULT_CSV = "results.csv"


def main(argv: List[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "compare":
        args = _compare_parser().parse_args(argv[1:])
        _run_compare(args)
        return
    if argv and argv[0] == "batch":
        args = _batch_parser().parse_args(argv[1:])
        _run_batch(args)
        return

    args = _search_parser().parse_args(argv)
    _run_single(args)


def run_from_busca(busca: Dict[str, Any]) -> None:
    network = load_network(busca["config"])
    result = search(
        network,
        start=busca["node_id"],
        resource=busca["resource_id"],
        ttl=int(busca["ttl"]),
        algo=busca["algo"],
        seed=busca.get("seed"),
        ignore_cache=bool(busca.get("ignore_cache", False)),
    )
    append_result_csv(busca.get("csv") or DEFAULT_CSV, result)
    print_result(result, trace=bool(busca.get("trace", False)))


def _search_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Busca em rede P2P nao estruturada.")
    parser.add_argument("config", help="Arquivo YAML da rede.")
    parser.add_argument("node_id", help="No inicial.")
    parser.add_argument("resource_id", help="Recurso buscado.")
    _common_options(parser)
    return parser


def _compare_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compara os quatro algoritmos de busca.")
    parser.add_argument("config", help="Arquivo YAML da rede.")
    parser.add_argument("--node", required=True, dest="node_id", help="No inicial.")
    parser.add_argument("--resource", required=True, dest="resource_id", help="Recurso buscado.")
    parser.add_argument("--ttl", type=int, default=3)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ignore-cache", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    return parser


def _batch_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa buscas em lote a partir de JSON.")
    parser.add_argument("config", help="Arquivo YAML da rede.")
    parser.add_argument("queries", help="Arquivo JSON com as buscas.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ignore-cache", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--csv", default=DEFAULT_CSV)
    return parser


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ttl", type=int, default=3)
    parser.add_argument("--algo", choices=sorted(ALGORITHMS), default="flooding")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--ignore-cache", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--csv", default=DEFAULT_CSV)


def _run_single(args: argparse.Namespace) -> None:
    _guarded(lambda: _single_result(args))


def _single_result(args: argparse.Namespace):
    network = load_network(args.config)
    result = search(
        network,
        start=args.node_id,
        resource=args.resource_id,
        ttl=args.ttl,
        algo=args.algo,
        seed=args.seed,
        ignore_cache=args.ignore_cache,
    )
    append_result_csv(args.csv, result)
    print_result(result, trace=args.trace)
    return result


def _run_compare(args: argparse.Namespace) -> None:
    def runner() -> None:
        network = load_network(args.config)
        for algo in ("flooding", "informed_flooding", "random_walk", "informed_random_walk"):
            result = search(
                network,
                start=args.node_id,
                resource=args.resource_id,
                ttl=args.ttl,
                algo=algo,
                seed=args.seed,
                ignore_cache=args.ignore_cache,
            )
            append_result_csv(args.csv, result)
            print_result(result, trace=args.trace)
            print()

    _guarded(runner)


def _run_batch(args: argparse.Namespace) -> None:
    def runner() -> None:
        network = load_network(args.config)
        for query in _load_queries(args.queries):
            result = search(
                network,
                start=query["node_id"],
                resource=query["resource_id"],
                ttl=int(query.get("ttl", 3)),
                algo=query.get("algo", "flooding"),
                seed=query.get("seed", args.seed),
                ignore_cache=bool(query.get("ignore_cache", args.ignore_cache)),
            )
            append_result_csv(args.csv, result)
            print_result(result, trace=args.trace)
            print()

    _guarded(runner)


def _load_queries(path: str) -> Iterable[Dict[str, Any]]:
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"Arquivo de lote nao encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON de lote invalido: {exc}") from exc

    if not isinstance(raw, list):
        raise ValueError("Arquivo de lote deve conter uma lista de buscas.")
    for index, query in enumerate(raw, start=1):
        if not isinstance(query, dict):
            raise ValueError(f"Busca #{index} invalida: deve ser um objeto.")
        missing = {"node_id", "resource_id"} - set(query)
        if missing:
            raise ValueError(f"Busca #{index} sem campos obrigatorios: {', '.join(sorted(missing))}.")
        yield query


def _guarded(action) -> None:
    try:
        action()
    except (ConfigError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

