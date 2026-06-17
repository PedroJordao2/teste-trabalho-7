```markdown
# Trabalho 7 - Busca em Redes P2P Nao Estruturadas

Este projeto implementa um simulador de busca em redes P2P nao estruturadas usando Python.

A rede e carregada a partir de arquivos YAML, e o sistema permite executar diferentes estrategias de busca por recursos, exibindo o rastro das mensagens trocadas entre os nos e salvando os resultados em CSV.

## Algoritmos Implementados

O projeto implementa quatro estrategias:

- `flooding`
- `informed_flooding`
- `random_walk`
- `informed_random_walk`

## Estrutura do Projeto

```text
trabalho7/
  p2p_search.py
  complex_graph.png
  results.csv

  p2p/
    __init__.py
    cli.py
    config.py
    models.py
    network.py
    output.py

  examples/
    complex.yaml
    mesh.yaml
    ring.yaml
    complex_queries.json
    queries.json
```

## Como Executar

Entre na pasta do projeto:

```powershell
cd C:\Users\pedro\Downloads\atividades-comp-distribuida-main\atividades-comp-distribuida-main\trabalho7
```

Se o comando `python` nao funcionar, use `py`.

## Exemplos com complex.yaml

### Flooding

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo flooding --trace --csv results.csv
```

### Informed Flooding

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo informed_flooding --trace --csv results.csv
```

### Random Walk

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo random_walk --seed 7 --trace --csv results.csv
```

### Informed Random Walk

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo informed_random_walk --seed 7 --trace --csv results.csv
```

## Comparar os Quatro Algoritmos

```powershell
py .\p2p_search.py compare .\examples\complex.yaml --node n1 --resource r8 --ttl 4 --trace --csv results.csv
```

## Execucao em Lote

O modo batch executa varias buscas definidas em um arquivo JSON:

```powershell
py .\p2p_search.py batch .\examples\complex.yaml .\examples\complex_queries.json --seed 7 --trace --csv results.csv
```

## Formato da Rede YAML

Exemplo:

```yaml
num_nodes: 3
min_neighbors: 1
max_neighbors: 2

resources:
  n1: r1, doc-a
  n2: r2, doc-b
  n3: r3, doc-c

caches:
  n2: r3=n3

edges:
  - n1, n2
  - n2, n3
```

## Rede complex.yaml

A rede `complex.yaml` possui 8 nos:

```text
n1 -> r1, doc-a
n2 -> r2, doc-b
n3 -> r3, doc-c
n4 -> r4, doc-d
n5 -> r5, doc-e
n6 -> r6, doc-f
n7 -> r7, r13
n8 -> r8, doc-h
```

Arestas:

```text
n1 -- n2
n1 -- n3
n2 -- n4
n2 -- n5
n3 -- n5
n3 -- n6
n4 -- n7
n5 -- n7
n6 -- n8
n7 -- n8
```

A imagem `complex_graph.png` mostra esse grafo visualmente.

## Trace de Eventos

Ao usar `--trace`, o programa mostra o rastro das mensagens:

```text
passo rodada tipo         origem   destino  ttl  recurso
--------------------------------------------------------
1     1      requisicao   n1       n2       3    r8
2     1      requisicao   n1       n3       3    r8
3     2      requisicao   n3       n6       2    r8
4     3      requisicao   n6       n8       1    r8
5     3      resposta     n8       n1       -    r8
6     3      backtracking n8       n6       -    r8
7     3      backtracking n6       n3       -    r8
8     3      backtracking n3       n1       -    r8
```

Tipos de evento:

```text
requisicao    mensagem de busca enviada
resposta      no encontrou o recurso e respondeu ao no inicial
direto        cache indicou diretamente o no que possui o recurso
backtracking  retorno pelo caminho
```

## TTL

`TTL` significa `Time To Live`.

Ele define o numero maximo de saltos da busca.

Exemplo com `--ttl 4`:

```text
n1 -> n3  TTL vira 3
n3 -> n6  TTL vira 2
n6 -> n8  TTL vira 1
```

Quando o TTL chega a zero, a mensagem nao continua sendo propagada.

## Seed

`--seed` controla a aleatoriedade nos algoritmos `random_walk` e `informed_random_walk`.

Com a mesma seed, o caminho sorteado e reproduzivel:

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo random_walk --seed 7 --trace
```

## CSV de Resultados

Toda busca gera ou atualiza um CSV.

Padrao:

```text
results.csv
```

Colunas:

```text
timestamp, algoritmo, no_inicial, recurso, ttl, encontrado, no_resposta, caminho, total_mensagens, total_nos
```

Exemplo:

```text
2026-06-14T19:54:02,flooding,n1,r8,4,true,n8,n1->n3->n6->n8,21,8
```

## Validacoes

Ao carregar a rede, o programa valida:

- rede conectada, sem particionamento
- limites `min_neighbors` e `max_neighbors`
- nenhum no sem recursos
- ausencia de aresta de um no para ele mesmo
- ausencia de referencias a nos desconhecidos
- ausencia de recursos duplicados
- caches apontando para recursos existentes
- caches apontando para nos que realmente possuem o recurso

## Execucao sem Argumentos

Tambem e possivel editar o objeto `BUSCA` em `p2p_search.py`:

```python
BUSCA = {
    "config": "examples/complex.yaml",
    "node_id": "n1",
    "resource_id": "r8",
    "ttl": 4,
    "algo": "flooding",
    "seed": None,
    "ignore_cache": False,
    "trace": True,
    "csv": "results.csv",
}
```

Depois execute:

```powershell
py .\p2p_search.py
```
```
