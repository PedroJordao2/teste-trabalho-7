# Trabalho 7 - Busca em Redes P2P Nao Estruturadas

Este projeto simula buscas em uma rede P2P nao estruturada. A rede e lida de um arquivo YAML, os algoritmos executam a busca por recurso e o programa mostra o rastro das mensagens no terminal.

O projeto tambem salva um resumo das execucoes em CSV.

## Estrutura

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

## Arquivo principal

O arquivo principal e:

```text
p2p_search.py
```

Ele pode ser executado pelo terminal ou pelo objeto `BUSCA` dentro do proprio arquivo.

## Como entrar na pasta

No terminal do VS Code:

```powershell
cd C:\Users\pedro\Downloads\atividades-comp-distribuida-main\atividades-comp-distribuida-main\trabalho7
```

Se `python` nao funcionar no Windows, use `py`.

## Grafo usado no exemplo principal

O arquivo principal dos testes e:

```text
examples/complex.yaml
```

Ele possui 8 nos:

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

As arestas sao nao direcionadas:

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

Tambem existe uma imagem do grafo:

```text
complex_graph.png
```

## Algoritmos disponiveis

O parametro `--algo` aceita:

```text
flooding
informed_flooding
random_walk
informed_random_walk
```

### flooding

Envia a requisicao para todos os vizinhos, respeitando o TTL.

Cada no encaminha para seus vizinhos, exceto o no de onde recebeu a mensagem. O `search_id` evita ciclos e impede que o mesmo no processe a mesma busca mais de uma vez.

Quando o recurso e encontrado, o no responde e aquele ramo para de encaminhar novas requisicoes.

### informed_flooding

Igual ao `flooding`, mas os nos intermediarios verificam o cache local.

Se um no sabe pelo cache onde esta o recurso, ele responde ao no inicial e mostra um evento `direto` para o no detentor.

### random_walk

Escolhe apenas um vizinho por vez de forma aleatoria.

Pode encontrar ou nao o recurso, dependendo das escolhas aleatorias e do TTL.

Use `--seed` para repetir o mesmo caminho.

### informed_random_walk

Igual ao `random_walk`, mas consulta cache antes de sortear o proximo vizinho.

## Comandos para testar os 4 algoritmos

Todos os exemplos abaixo usam:

```text
rede: examples/complex.yaml
origem: n1
recurso: r8
ttl: 4
```

### 1. Flooding

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo flooding --trace --csv results.csv
```

### 2. Informed Flooding

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo informed_flooding --trace --csv results.csv
```

### 3. Random Walk

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo random_walk --seed 7 --trace --csv results.csv
```

### 4. Informed Random Walk

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo informed_random_walk --seed 7 --trace --csv results.csv
```

## Comparar os 4 algoritmos de uma vez

```powershell
py .\p2p_search.py compare .\examples\complex.yaml --node n1 --resource r8 --ttl 4 --trace --csv results.csv
```

## Execucao em lote

O modo batch executa varias buscas descritas em um arquivo JSON.

```powershell
py .\p2p_search.py batch .\examples\complex.yaml .\examples\complex_queries.json --seed 7 --trace --csv results.csv
```

## O que e TTL

TTL significa `Time To Live`.

No projeto, ele representa o limite de saltos da busca.

Exemplo com `--ttl 4`:

```text
n1 -> n3  TTL vira 3
n3 -> n6  TTL vira 2
n6 -> n8  TTL vira 1
```

Quando o TTL chega a zero, a mensagem nao continua sendo propagada.

## O que e seed

`--seed` controla a aleatoriedade do `random_walk`.

Com a mesma seed, o caminho sorteado tende a ser o mesmo:

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo random_walk --seed 7 --trace
```

Mudando a seed, o caminho pode mudar:

```powershell
py .\p2p_search.py .\examples\complex.yaml n1 r8 --ttl 4 --algo random_walk --seed 2 --trace
```

## Trace de eventos

Use `--trace` para mostrar o rastro das mensagens.

Tipos de evento:

```text
requisicao    mensagem de busca enviada de um no para outro
resposta      no encontrou o recurso e respondeu ao no inicial
direto        cache indicou diretamente o no detentor do recurso
backtracking  retorno pelo caminho depois de sucesso ou fim de ramo
```

Exemplo:

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

Observacao: mensagens internas ignoradas por `search_id` nao sao exibidas no trace, para deixar a saida mais limpa.

## CSV de resultados

Toda busca salva ou atualiza um CSV.

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

## Formato do YAML

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

Regras importantes:

- A rede nao pode estar particionada.
- Todo no deve respeitar `min_neighbors` e `max_neighbors`.
- Nenhum no pode ficar sem recursos.
- Nao pode haver aresta de um no para ele mesmo.
- Nao pode haver referencia a no inexistente.
- Um recurso nao pode aparecer em mais de um no.
- Cache deve apontar para um recurso existente e para o no que realmente possui esse recurso.

## Execucao sem terminal completo

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

Depois rode:

```powershell
py .\p2p_search.py
```
