from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class MessageEvent:
    passo: int
    search_id: str
    rodada: Optional[int]
    tipo: str
    origem: str
    destino: str
    recurso: str
    ttl: Optional[int]


@dataclass(frozen=True)
class SearchResult:
    search_id: str
    algoritmo: str
    no_inicial: str
    recurso: str
    ttl: int
    encontrado: bool
    no_resposta: Optional[str]
    no_detentor: Optional[str]
    respondido_por_cache: Optional[str]
    caminho: List[str]
    total_mensagens: int
    total_nos: int
    eventos: List[MessageEvent] = field(default_factory=list)


@dataclass
class P2PNetwork:
    num_nodes: int
    min_neighbors: int
    max_neighbors: int
    resources: Dict[str, Set[str]]
    caches: Dict[str, Dict[str, str]]
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)

    @property
    def nodes(self) -> Set[str]:
        return set(self.resources)

    def has_resource(self, node_id: str, resource_id: str) -> bool:
        return resource_id in self.resources.get(node_id, set())

    def owner_of(self, resource_id: str) -> Optional[str]:
        for node_id, resources in self.resources.items():
            if resource_id in resources:
                return node_id
        return None

    def neighbors(self, node_id: str) -> List[str]:
        return sorted(self.adjacency.get(node_id, set()))
