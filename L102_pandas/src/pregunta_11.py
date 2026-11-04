def pregunta_11():
    """
    En `data/tbl1.tsv`, cada valor de la columna `c0` aparece en varias
    filas, una por cada letra de la columna `c4`. Construya un DataFrame con
    una fila por cada valor de `c0`, en orden ascendente, y las columnas `c0`
    y `c4`. En `c4`, escriba las letras de ese `c0` ordenadas alfabéticamente
    y separadas por comas.

    Ejemplo del formato de la respuesta:

            c0       c4
        0    0    b,f,g
        1    1    a,c,f
        2    2  a,c,e,f
        ...
    """

    import pandas as pd

    tbl1 = pd.read_csv("data/tbl1.tsv", sep="\t")

    # Se ordena por c0 y por c4 para que las letras queden en orden alfabético
    tbl1 = tbl1.sort_values(["c0", "c4"])

    # Para cada c0 se unen sus letras separadas por comas
    resultado = tbl1.groupby("c0")["c4"].apply(lambda x: ",".join(x))

    # c0 pasa de ser índice a ser una columna normal
    resultado = resultado.reset_index()

    return resultado
