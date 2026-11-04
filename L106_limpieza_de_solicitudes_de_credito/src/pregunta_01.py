import pandas as pd
from pathlib import Path

def pregunta_01():
    # El error de tokenización se soluciona usando el separador correcto (;)
    df = pd.read_csv("data/solicitudes_de_credito.csv.gz", sep=";", index_col=0)
    
    columnas = [
        "sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", 
        "estrato", "comuna_ciudadano", "fecha_de_beneficio", 
        "monto_del_credito", "línea_credito"
    ]
    df = df[columnas].copy()
    
    # Eliminar registros incompletos (excepto en 'comuna_ciudadano')
    columnas_req = [c for c in columnas if c != "comuna_ciudadano"]
    df.dropna(subset=columnas_req, inplace=True)
    
    # Estandarizar columnas de texto: minúsculas, reemplazar '-' y '_' por espacios, y quitar espacios extra
    text_cols = ["sexo", "tipo_de_emprendimiento", "idea_negocio", "barrio", "línea_credito"]
    for col in text_cols:
        df[col] = (df[col].astype(str).str.lower()
                          .str.replace(r'[\-_]', ' ', regex=True)
                          .str.replace(r'\s+', ' ', regex=True)
                          .str.strip())
        
    # Estandarizar el monto: eliminar '.00' o ',00' al final, quitar símbolos no numéricos y pasar a entero
    df["monto_del_credito"] = (df["monto_del_credito"].astype(str)
                               .str.replace(r'\.00$|,00$', '', regex=True)
                               .str.replace(r'[^\d]', '', regex=True)
                               .astype(int))
    
    # Estandarizar estrato a número entero
    df["estrato"] = df["estrato"].astype(int)
    
    # Estandarizar fechas unificando los formatos mezclados a AAAA-MM-DD
    fechas = pd.to_datetime(df["fecha_de_beneficio"], format="%d/%m/%Y", errors="coerce")
    fechas = fechas.fillna(pd.to_datetime(df["fecha_de_beneficio"], format="%Y-%m-%d", errors="coerce"))
    fechas = fechas.fillna(pd.to_datetime(df["fecha_de_beneficio"], format="%Y/%m/%d", errors="coerce"))
    df["fecha_de_beneficio"] = fechas.dt.strftime("%Y-%m-%d")
    
    # Descartar si por alguna razón la fecha no se pudo parsear
    df.dropna(subset=["fecha_de_beneficio"], inplace=True)
    
    # Eliminar los registros duplicados DESPUÉS de estandarizar, para atraparlos correctamente
    df.drop_duplicates(inplace=True)
    
    # Guardar en submission con separador de punto y coma y sin index
    out_dir = Path("submission")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "solicitudes_de_credito.csv", sep=";", index=False)