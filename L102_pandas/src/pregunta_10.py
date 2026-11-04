def pregunta_10():
    """
    Usando `data/tbl0.tsv`, construya para cada categoría de la columna `c1`
    un texto con todos sus valores de la columna `c2`, ordenados de menor a
    mayor y separados por `:`. Retorne un DataFrame cuyo índice son las
    categorías, en orden alfabético, con una única columna llamada `c2`.

    Ejemplo del formato de la respuesta:

                           c2
        c1
        A     1:1:2:3:6:7:8:9
        B       1:3:4:5:6:8:9
        C           0:5:6:7:9
        ...
    """

    import pandas as pd

    tbl0 = pd.read_csv("data/tbl0.tsv", sep="\t")

    # Se ordena por c1 y por c2 mientras c2 todavía es número,
    # así los valores quedan de menor a mayor dentro de cada categoría
    tbl0 = tbl0.sort_values(["c1", "c2"])

    # c2 se pasa a texto para poder unirlo con ":"
    tbl0["c2"] = tbl0["c2"].astype(str)

    # Se une cada grupo en un solo texto separado por ":"
    resultado = tbl0.groupby("c1")["c2"].apply(lambda x: ":".join(x))

    # La Serie se convierte en DataFrame con la columna c2
    return resultado.to_frame()
