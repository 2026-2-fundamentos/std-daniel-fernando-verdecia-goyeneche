import gzip
from pathlib import Path

def _abrir_archivo():
    base = Path(__file__).resolve()
    for p in [base.parent] + list(base.parents):
        for n in ["data.csv", "data/data.csv", "data.csv.gz", "data/data.csv.gz"]:
            f = p / n
            if f.is_file():
                return gzip.open(f, "rt", encoding="utf-8") if n.endswith(".gz") else open(f, "r", encoding="utf-8")
        encontrados = list(p.glob("**/data.csv*"))
        if encontrados:
            f = encontrados[0]
            return gzip.open(f, "rt", encoding="utf-8") if f.name.endswith(".gz") else open(f, "r", encoding="utf-8")
    return open("data.csv", "r", encoding="utf-8")

def pregunta_10():
    salida = []
    with _abrir_archivo() as f:
        for linea in f:
            columnas = linea.strip().split("\t")
            letra = columnas[0]
            num_codigos = len(columnas[3].split(","))
            num_metricas = len(columnas[4].split(","))
            salida.append((letra, num_codigos, num_metricas))
    return salida