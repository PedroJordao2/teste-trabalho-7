import sys

from p2p.cli import main, run_from_busca


BUSCA = {
    "config": "examples/complex.yaml",
    "node_id": "n1",
    "resource_id": "r5",
    "ttl": 3,
    "algo": "flooding",
    "seed": None,
    "ignore_cache": False,
    "trace": True,
    "csv": "results.csv",
}


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_from_busca(BUSCA)
    else:
        main()
