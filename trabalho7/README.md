# Trabalho 7 — Busca em Redes P2P Não Estruturadas

Simulador de algoritmos de busca em redes P2P não estruturadas, desenvolvido em Python. Suporta quatro estratégias de busca (flooding, flooding informado, random walk e random walk informado) com rastreamento de mensagens e exportação de resultados em CSV.

---

## Estrutura do projeto

```
trabalho7/
├── p2p_search.py          # Ponto de entrada principal
├── results.csv            # Resultados das buscas executadas
├── examples/
│   ├── complex.yaml       # Rede de 8 nós com caches
│   ├── mesh.yaml          # Topologia em malha
│   ├── ring.yaml          # Topologia em anel
│   ├── queries.json       # Consultas simples em lote
│   └── complex_queries.json
└── p2p/
    ├── __init__.py
    ├── cli.py             # Interface de linha de comando
    ├── config.py          # Leitura e validação do arquivo YAML de rede
    ├── models.py          # Modelos de dados (rede, resultado, eventos)
    ├── network.py         # Implementação dos algoritmos de busca
    └── output.py          # Impressão de resultados e escrita em CSV
```

---

## Requisitos

- Python 3.10 ou superior (uso de `X | Y` em type hints)
- Nenhuma dependência externa — biblioteca padrão apenas

---

## Instalação

```bash
# Clone ou descompacte o projeto e entre no diretório raiz
cd trabalho7
```

Nenhuma instalação adicional é necessária.

---

## Uso

### Busca simples

```bash
python p2p_search.py <rede.yaml> <no_inicial> <recurso> [opções]
```

**Exemplo:**
```bash
python p2p_search.py examples/complex.yaml n1 r5 --algo flooding --ttl 3 --trace
```

### Comparar os quatro algoritmos

Executa todos os algoritmos para a mesma busca e exibe os resultados lado a lado.

```bash
python p2p_search.py compare <rede.yaml> --node <no> --resource <recurso> [opções]
```

**Exemplo:**
```bash
python p2p_search.py compare examples/complex.yaml --node n1 --resource r5 --ttl 4 --trace
```

### Execução em lote (batch)

Lê uma lista de buscas de um arquivo JSON e executa todas em sequência.

```bash
python p2p_search.py batch <rede.yaml> <queries.json> [opções]
```

**Exemplo:**
```bash
python p2p_search.py batch examples/complex.yaml examples/queries.json --trace
```

### Execução direta (sem argumentos)

Executar `python p2p_search.py` sem argumentos roda a busca pré-configurada no dicionário `BUSCA` dentro de `p2p_search.py`.

---

## Opções comuns

| Opção | Padrão | Descrição |
|---|---|---|
| `--algo` | `flooding` | Algoritmo: `flooding`, `informed_flooding`, `random_walk`, `informed_random_walk` |
| `--ttl` | `3` | Número máximo de saltos (Time To Live) |
| `--seed` | `None` | Semente para reprodutibilidade do random walk |
| `--ignore-cache` | `False` | Ignora entradas de cache nos nós |
| `--trace` | `False` | Exibe o rastreamento de mensagens passo a passo |
| `--csv` | `results.csv` | Arquivo CSV para salvar os resultados |

---

## Algoritmos implementados

| Algoritmo | Descrição |
|---|---|
| `flooding` | Inunda toda a rede até o limite de TTL |
| `informed_flooding` | Flooding com uso de cache nos nós intermediários |
| `random_walk` | Percorre a rede por caminho aleatório |
| `informed_random_walk` | Random walk com uso de cache nos nós intermediários |

---

## Formato da rede (YAML)

O arquivo de configuração da rede deve ser um `.yaml` com os seguintes campos:

```yaml
num_nodes: 8
min_neighbors: 2
max_neighbors: 4

resources:
  n1: r1, doc-a
  n2: r2, doc-b
  n5: r5, doc-e

caches:           # opcional
  n2: r5=n5       # n2 sabe que r5 está em n5

edges:
  - n1, n2
  - n1, n3
  - n2, n5
```

**Regras de validação:**
- Cada recurso pertence a exatamente um nó.
- Todo nó deve ter ao menos `min_neighbors` e no máximo `max_neighbors` vizinhos.
- A rede deve ser conectada (sem partições).
- Entradas de cache devem apontar para o nó real detentor do recurso.

---

## Formato do arquivo de queries (JSON)

```json
[
  {"node_id": "n1", "resource_id": "r5", "ttl": 4, "algo": "flooding"},
  {"node_id": "n1", "resource_id": "r5", "ttl": 2, "algo": "random_walk"},
  {"node_id": "n3", "resource_id": "r1", "ttl": 3, "algo": "informed_flooding"}
]
```

Campos obrigatórios: `node_id`, `resource_id`. Os demais são opcionais.

---

## Saída CSV

Os resultados são acumulados em `results.csv` com as colunas:

```
timestamp, algoritmo, no_inicial, recurso, ttl, encontrado, no_resposta, caminho, total_mensagens, total_nos
```

**Exemplo de linha:**
```
2026-06-14T19:43:06,flooding,n1,r5,3,true,n5,n1->n2->n5,8,8
```
