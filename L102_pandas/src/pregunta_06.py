def pregunta_06():
    """
    Usando `data/tbl1.tsv`, obtenga los valores distintos de la columna `c4`,
    conviértalos a mayúsculas y retórnelos como una lista ordenada
    alfabéticamente.

    Ejemplo del formato de la respuesta:

        ["A", "B", "C", "D", "E", "F", "G"]
    """

    import pandas as pd

    tbl1 = pd.read_csv("data/tbl1.tsv", sep="\t")

    # Primero se pasa todo a mayúsculas y luego se sacan los valores distintos
    letras = tbl1["c4"].str.upper().unique()

    # Se ordenan alfabéticamente y se devuelven como lista
    return sorted(letras)
