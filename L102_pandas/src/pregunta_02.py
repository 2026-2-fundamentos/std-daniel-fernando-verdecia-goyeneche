def pregunta_02():
    """
    ¿Cuántas columnas tiene la tabla `data/tbl0.tsv`? Retorne la cantidad
    como un número entero.

    Ejemplo del formato de la respuesta:

        4
    """

    import pandas as pd

    # Se lee la tabla, las columnas están separadas por tabuladores
    tbl0 = pd.read_csv("data/tbl0.tsv", sep="\t")

    # La cantidad de columnas es la segunda posición de shape
    return tbl0.shape[1]
