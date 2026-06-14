from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from .models import P2PNetwork


class ConfigError(ValueError):
    pass


REQUIRED_FIELDS = {"num_nodes", "min_neighbors", "max_neighbors", "resources", "edges"}


def load_network(path: str) -> P2PNetwork:
    config_path = Path(path)
    if config_path.suffix.lower() not in {".yaml", ".yml"}:
        raise ConfigError("Formato invalido: a rede deve ser informada somente em YAML (.yaml ou .yml).")

    try:
        raw = _load_simple_yaml(config_path)
    except FileNotFoundError as exc:
        raise ConfigError(f"Arquivo de configuracao nao encontrado: {path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Configuracao invalida: o YAML deve conter um mapa no topo.")

    missing = REQUIRED_FIELDS - set(raw)
    if missing:
        raise ConfigError(f"Campos obrigatorios ausentes: {', '.join(sorted(missing))}.")

    num_nodes = _positive_int(raw["num_nodes"], "num_nodes")
    min_neighbors = _non_negative_int(raw["min_neighbors"], "min_neighbors")
    max_neighbors = _non_negative_int(raw["max_neighbors"], "max_neighbors")
    if min_neighbors > max_neighbors:
        raise ConfigError("Campo invalido: min_neighbors nao pode ser maior que max_neighbors.")

    resources = _parse_resources(raw["resources"])
    caches = _parse_caches(raw.get("caches", {}))
    adjacency = _parse_edges(raw["edges"], resources.keys())

    network = P2PNetwork(
        num_nodes=num_nodes,
        min_neighbors=min_neighbors,
        max_neighbors=max_neighbors,
        resources=resources,
        caches=caches,
        adjacency=adjacency,
    )
    _validate_network(network)
    return network


def _load_simple_yaml(path: Path) -> Dict[str, Any]:
    """Carrega o subconjunto de YAML usado nos arquivos da atividade."""
    data: Dict[str, Any] = {}
    current_key: str | None = None

    with path.open("r", encoding="utf-8") as file:
        for line_number, original in enumerate(file, start=1):
            line = original.split("#", 1)[0].rstrip()
            if not line.strip():
                continue

            if not line.startswith(" "):
                current_key = None
                if ":" not in line:
                    raise ConfigError(f"YAML invalido na linha {line_number}: esperado chave: valor.")
                key, value = [part.strip() for part in line.split(":", 1)]
                if not key:
                    raise ConfigError(f"YAML invalido na linha {line_number}: chave vazia.")
                if value == "":
                    current_key = key
                    data[key] = []
                else:
                    data[key] = _scalar(value)
                continue

            if current_key is None:
                raise ConfigError(f"YAML invalido na linha {line_number}: indentacao inesperada.")

            item = line.strip()
            if item.startswith("- "):
                if not isinstance(data[current_key], list):
                    raise ConfigError(f"YAML invalido na linha {line_number}: lista inesperada.")
                data[current_key].append(item[2:].strip())
                continue

            if ":" not in item:
                raise ConfigError(f"YAML invalido na linha {line_number}: esperado chave: valor.")
            key, value = [part.strip() for part in item.split(":", 1)]
            if isinstance(data[current_key], list) and not data[current_key]:
                data[current_key] = {}
            if not isinstance(data[current_key], dict):
                raise ConfigError(f"YAML invalido na linha {line_number}: mapa inesperado.")
            data[current_key][key] = value

    return data


def _scalar(value: str) -> Any:
    try:
        return int(value)
    except ValueError:
        return value


def _positive_int(value: Any, field: str) -> int:
    parsed = _non_negative_int(value, field)
    if parsed <= 0:
        raise ConfigError(f"Campo invalido: {field} deve ser inteiro positivo.")
    return parsed


def _non_negative_int(value: Any, field: str) -> int:
    if not isinstance(value, int):
        raise ConfigError(f"Campo invalido: {field} deve ser inteiro.")
    if value < 0:
        raise ConfigError(f"Campo invalido: {field} nao pode ser negativo.")
    return value


def _parse_resources(raw: Any) -> Dict[str, Set[str]]:
    if not isinstance(raw, dict) or not raw:
        raise ConfigError("Campo invalido: resources deve ser um mapa nao vazio.")

    parsed: Dict[str, Set[str]] = {}
    seen: Dict[str, str] = {}
    for node_id, value in raw.items():
        node = _node_id(node_id, "resources")
        items = _split_items(value, f"resources.{node}")
        if not items:
            raise ConfigError(f"Nenhum no pode ficar sem recursos: {node}.")
        resources = set(items)
        if len(resources) != len(items):
            raise ConfigError(f"Recursos duplicados no proprio no {node}.")
        for resource in resources:
            if resource in seen:
                raise ConfigError(f"Recurso duplicado em mais de um no: {resource} em {seen[resource]} e {node}.")
            seen[resource] = node
        parsed[node] = resources
    return parsed


def _parse_caches(raw: Any) -> Dict[str, Dict[str, str]]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ConfigError("Campo invalido: caches deve ser um mapa.")

    parsed: Dict[str, Dict[str, str]] = {}
    for node_id, value in raw.items():
        node = _node_id(node_id, "caches")
        entries = _split_items(value, f"caches.{node}") if value not in (None, "") else []
        cache: Dict[str, str] = {}
        for entry in entries:
            if "=" not in entry:
                raise ConfigError(f"Cache invalido em {node}: use recurso=no, exemplo r3=n3.")
            resource, owner = [part.strip() for part in entry.split("=", 1)]
            if not resource or not owner:
                raise ConfigError(f"Cache invalido em {node}: recurso e no devem ser preenchidos.")
            cache[resource] = owner
        parsed[node] = cache
    return parsed


def _parse_edges(raw: Any, known_nodes: Iterable[str]) -> Dict[str, Set[str]]:
    known = set(known_nodes)
    if not isinstance(raw, list):
        raise ConfigError("Campo invalido: edges deve ser uma lista.")

    adjacency = {node: set() for node in known}
    for item in raw:
        left, right = _parse_edge(item)
        if left == right:
            raise ConfigError(f"Aresta invalida: no nao pode apontar para ele mesmo ({left}).")
        for node in (left, right):
            if node not in known:
                raise ConfigError(f"Referencia a no desconhecido em edges: {node}.")
        adjacency[left].add(right)
        adjacency[right].add(left)
    return adjacency


def _parse_edge(item: Any) -> Tuple[str, str]:
    if isinstance(item, str):
        parts = [part.strip() for part in item.split(",")]
    elif isinstance(item, list):
        parts = [str(part).strip() for part in item]
    else:
        raise ConfigError("Aresta invalida: use 'n1, n2' ou [n1, n2].")
    if len(parts) != 2 or not all(parts):
        raise ConfigError(f"Aresta invalida: {item}.")
    return parts[0], parts[1]


def _split_items(value: Any, field: str) -> List[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ConfigError(f"Campo invalido: {field} deve ser string separada por virgulas ou lista.")


def _node_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"No invalido em {field}.")
    return value.strip()


def _validate_network(network: P2PNetwork) -> None:
    nodes = network.nodes
    if len(nodes) != network.num_nodes:
        raise ConfigError(
            f"num_nodes invalido: esperado {network.num_nodes}, mas resources define {len(nodes)} nos."
        )

    for node in network.caches:
        if node not in nodes:
            raise ConfigError(f"Referencia a no desconhecido em caches: {node}.")

    for node in nodes:
        degree = len(network.adjacency.get(node, set()))
        if degree < network.min_neighbors or degree > network.max_neighbors:
            raise ConfigError(
                f"No {node} viola limites de vizinhos: possui {degree}, "
                f"min={network.min_neighbors}, max={network.max_neighbors}."
            )

    for node, cache in network.caches.items():
        for resource, owner in cache.items():
            if owner not in nodes:
                raise ConfigError(f"Cache de {node} aponta para no desconhecido: {owner}.")
            real_owner = network.owner_of(resource)
            if real_owner is None:
                raise ConfigError(f"Cache de {node} aponta para recurso inexistente: {resource}.")
            if real_owner != owner:
                raise ConfigError(
                    f"Cache de {node} invalido: {owner} nao possui {resource}; dono correto e {real_owner}."
                )

    if not _is_connected(network):
        raise ConfigError("Rede particionada: deve haver caminho entre quaisquer dois nos.")


def _is_connected(network: P2PNetwork) -> bool:
    nodes = network.nodes
    start = next(iter(nodes))
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in network.adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == nodes
