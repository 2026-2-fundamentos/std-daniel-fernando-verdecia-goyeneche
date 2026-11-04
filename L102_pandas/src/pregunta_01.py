def pregunta_01():
    """
    ¿Cuántos registros tiene la tabla `data/tbl0.tsv`? Retorne la cantidad
    como un número entero.

    Ejemplo del formato de la respuesta:

        40
    """

    import pandas as pd

    # Se lee la tabla, las columnas están separadas por tabuladores
    tbl0 = pd.read_csv("data/tbl0.tsv", sep="\t")

    # La cantidad de registros es la cantidad de filas
    return tbl0.shape[0]
