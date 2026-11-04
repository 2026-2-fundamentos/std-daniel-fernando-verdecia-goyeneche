def pregunta_12():
    """
    En `data/tbl2.tsv`, cada valor de la columna `c0` aparece en varias
    filas. Construya un DataFrame con una fila por cada valor de `c0`, en
    orden ascendente, y las columnas `c0` y `c5`. En `c5`, forme un texto
    `c5a:c5b` para cada fila de ese `c0`, ordene esos textos alfabéticamente y
    únalos separados por comas.

    Ejemplo del formato de la respuesta:

            c0                             c5
        0    0  bbb:0,ddd:9,ggg:8,hhh:2,jjj:3
        1    1        aaa:3,ccc:2,ddd:0,hhh:9
        2    2        ccc:6,ddd:2,ggg:5,jjj:1
        ...
    """

    import pandas as pd

    tbl2 = pd.read_csv("data/tbl2.tsv", sep="\t")

    # Se forma el texto c5a:c5b en cada fila (c5b es número, se pasa a texto)
    tbl2["c5"] = tbl2["c5a"] + ":" + tbl2["c5b"].astype(str)

    # Se ordena por c0 y por el texto c5 para que queden en orden alfabético
    tbl2 = tbl2.sort_values(["c0", "c5"])

    # Para cada c0 se unen los textos separados por comas
    resultado = tbl2.groupby("c0")["c5"].apply(lambda x: ",".join(x))

    # c0 pasa de ser índice a ser una columna normal
    resultado = resultado.reset_index()

    return resultado
