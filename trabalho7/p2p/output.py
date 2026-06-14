import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import SearchResult


CSV_COLUMNS = [
    "timestamp",
    "algoritmo",
    "no_inicial",
    "recurso",
    "ttl",
    "encontrado",
    "no_resposta",
    "caminho",
    "total_mensagens",
    "total_nos",
]


def append_result_csv(path: str, result: SearchResult) -> None:
    csv_path = Path(path)
    should_write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        if should_write_header:
            writer.writeheader()
        writer.writerow(_row(result))


def append_many_csv(path: str, results: Iterable[SearchResult]) -> None:
    for result in results:
        append_result_csv(path, result)


def print_result(result: SearchResult, trace: bool = False) -> None:
    status = "encontrado" if result.encontrado else "nao encontrado"
    cache_info = result.respondido_por_cache or "-"
    print(f"Algoritmo: {result.algoritmo}")
    print(f"Search ID: {result.search_id}")
    print(f"Recurso {result.recurso}: {status}")
    print(f"No inicial: {result.no_inicial}")
    print(f"No resposta: {result.no_resposta or '-'}")
    print(f"No detentor: {result.no_detentor or '-'}")
    print(f"Resposta via cache: {cache_info}")
    print(f"Caminho: {_path(result.caminho) or '-'}")
    print(f"Total de mensagens: {result.total_mensagens}")
    print(f"Total de nos envolvidos: {result.total_nos}")
    if trace:
        print(f"TTL: {result.ttl}")
        print_trace(result)


def print_trace(result: SearchResult) -> None:
    print("Rastro de eventos:")
    if not result.eventos:
        print("  nenhuma mensagem trocada")
        return

    header = f"{'passo':<5} {'rodada':<6} {'tipo':<10} {'origem':<8} {'destino':<8} {'ttl':<4} recurso"
    print(header)
    print("-" * len(header))
    for event in result.eventos:
        rodada = "-" if event.rodada is None else str(event.rodada)
        ttl = "-" if event.ttl is None else str(event.ttl)
        print(
            f"{event.passo:<5} {rodada:<6} {event.tipo:<10} "
            f"{event.origem:<8} {event.destino:<8} {ttl:<4} {event.recurso}"
        )


def _row(result: SearchResult) -> dict:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "algoritmo": result.algoritmo,
        "no_inicial": result.no_inicial,
        "recurso": result.recurso,
        "ttl": result.ttl,
        "encontrado": str(result.encontrado).lower(),
        "no_resposta": result.no_resposta or "",
        "caminho": _path(result.caminho) if result.encontrado else "",
        "total_mensagens": result.total_mensagens,
        "total_nos": result.total_nos,
    }


def _path(path: list[str]) -> str:
    return "->".join(path)
