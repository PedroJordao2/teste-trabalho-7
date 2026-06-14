import random
import uuid
from collections import deque
from typing import Iterable, List, Optional, Set, Tuple

from .models import MessageEvent, P2PNetwork, SearchResult


ALGORITHMS = {"flooding", "informed_flooding", "random_walk", "informed_random_walk"}


def search(
    network: P2PNetwork,
    start: str,
    resource: str,
    ttl: int,
    algo: str,
    seed: Optional[int] = None,
    ignore_cache: bool = False,
) -> SearchResult:
    if algo not in ALGORITHMS:
        raise ValueError(f"Algoritmo invalido: {algo}. Use: {', '.join(sorted(ALGORITHMS))}.")
    if start not in network.nodes:
        raise ValueError(f"No inicial desconhecido: {start}.")
    if ttl < 0:
        raise ValueError("TTL deve ser maior ou igual a zero.")

    if algo == "flooding":
        return _flooding(network, start, resource, ttl, algo, use_cache=False)
    if algo == "informed_flooding":
        return _flooding(network, start, resource, ttl, algo, use_cache=not ignore_cache)
    if algo == "random_walk":
        return _random_walk(network, start, resource, ttl, algo, seed, use_cache=False)
    return _random_walk(network, start, resource, ttl, algo, seed, use_cache=not ignore_cache)


def _flooding(
    network: P2PNetwork,
    start: str,
    resource: str,
    ttl: int,
    algo: str,
    use_cache: bool,
) -> SearchResult:
    search_id = str(uuid.uuid4())
    involved: Set[str] = {start}
    events: List[MessageEvent] = []
    found_path: List[str] = []
    responder: Optional[str] = None
    holder: Optional[str] = None
    informed_by: Optional[str] = None

    queue = deque([(start, [start], ttl)])
    seen = {start}

    while queue:
        node, path, remaining = queue.popleft()
        rodada = ttl - remaining

        candidate = _direct_response(network, node, resource, path, node)
        if candidate and responder is None:
            responder, holder, informed_by, found_path = candidate
            _add_event(events, search_id, rodada, "resposta", responder, start, resource, None)

        if use_cache and node != start:
            candidate = _cache_response(network, node, resource, path)
            if candidate:
                cache_responder, cache_holder, cache_informer, cache_path = candidate
                _add_event(events, search_id, rodada, "resposta", cache_responder, start, resource, None)
                _add_event(events, search_id, rodada, "direto", cache_responder, cache_holder, resource, None)
                if responder is None:
                    responder = cache_responder
                    holder = cache_holder
                    informed_by = cache_informer
                    found_path = cache_path

        if remaining == 0:
            continue

        for neighbor in network.neighbors(node):
            if neighbor in seen:
                continue
            _add_event(events, search_id, rodada + 1, "requisicao", node, neighbor, resource, remaining - 1)
            involved.add(neighbor)
            seen.add(neighbor)
            queue.append((neighbor, path + [neighbor], remaining - 1))

    return _result(algo, start, resource, ttl, responder, holder, informed_by, found_path, events, involved, search_id)


def _random_walk(
    network: P2PNetwork,
    start: str,
    resource: str,
    ttl: int,
    algo: str,
    seed: Optional[int],
    use_cache: bool,
) -> SearchResult:
    search_id = str(uuid.uuid4())
    rng = random.Random(seed)
    involved: Set[str] = {start}
    events: List[MessageEvent] = []
    node = start
    path = [start]

    for step in range(ttl + 1):
        candidate = _direct_response(network, node, resource, path, node)
        if candidate:
            responder, holder, informed_by, found_path = candidate
            _add_event(events, search_id, step, "resposta", responder, start, resource, None)
            return _result(
                algo, start, resource, ttl, responder, holder, informed_by, found_path, events, involved, search_id
            )

        if use_cache and node != start:
            candidate = _cache_response(network, node, resource, path)
            if candidate:
                responder, holder, informed_by, found_path = candidate
                _add_event(events, search_id, step, "resposta", responder, start, resource, None)
                _add_event(events, search_id, step, "direto", responder, holder, resource, None)
                involved.add(holder)
                return _result(
                    algo, start, resource, ttl, responder, holder, informed_by, found_path, events, involved, search_id
                )

        if step == ttl:
            break

        neighbors = network.neighbors(node)
        if not neighbors:
            break
        next_node = rng.choice(neighbors)
        _add_event(events, search_id, step + 1, "requisicao", node, next_node, resource, ttl - step - 1)
        node = next_node
        involved.add(node)
        path.append(node)

    return _result(algo, start, resource, ttl, None, None, None, [], events, involved, search_id)


def _direct_response(
    network: P2PNetwork,
    node: str,
    resource: str,
    path: List[str],
    responder: str,
) -> Optional[Tuple[str, str, Optional[str], List[str]]]:
    if network.has_resource(node, resource):
        return responder, node, None, path
    return None


def _cache_response(
    network: P2PNetwork,
    node: str,
    resource: str,
    path: List[str],
) -> Optional[Tuple[str, str, str, List[str]]]:
    owner = network.caches.get(node, {}).get(resource)
    if owner and network.has_resource(owner, resource):
        return node, owner, node, path + [owner]
    return None


def _add_event(
    events: List[MessageEvent],
    search_id: str,
    rodada: Optional[int],
    tipo: str,
    origem: str,
    destino: str,
    recurso: str,
    ttl: Optional[int],
) -> None:
    events.append(
        MessageEvent(
            passo=len(events) + 1,
            search_id=search_id,
            rodada=rodada,
            tipo=tipo,
            origem=origem,
            destino=destino,
            recurso=recurso,
            ttl=ttl,
        )
    )


def _result(
    algo: str,
    start: str,
    resource: str,
    ttl: int,
    responder: Optional[str],
    holder: Optional[str],
    informed_by: Optional[str],
    path: List[str],
    events: List[MessageEvent],
    involved: Iterable[str],
    search_id: str,
) -> SearchResult:
    return SearchResult(
        search_id=search_id,
        algoritmo=algo,
        no_inicial=start,
        recurso=resource,
        ttl=ttl,
        encontrado=responder is not None,
        no_resposta=responder,
        no_detentor=holder,
        respondido_por_cache=informed_by,
        caminho=path if responder else [],
        total_mensagens=len(events),
        total_nos=len(set(involved)),
        eventos=events,
    )
