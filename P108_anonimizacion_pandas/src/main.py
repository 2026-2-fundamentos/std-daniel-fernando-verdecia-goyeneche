import pandas as pd
import hashlib
from pathlib import Path

def generar_customer_id(doc_id):
    """
    Genera un ID único y determinista usando SHA-256 basado en el document_id.
    Cumple el formato requerido: CUST-[0-9A-F]{12}
    """
    hash_hex = hashlib.sha256(str(doc_id).encode('utf-8')).hexdigest().upper()
    return f"CUST-{hash_hex[:12]}"

def main():
    # .parents[1] sube un nivel para salir de 'src/' y ubicarse en 'P108_anonimizacion_pandas/'
    base_dir = Path(__file__).resolve().parents[1]
    
    raw_file = base_dir / "data" / "raw.csv"
    submission_dir = base_dir / "submission"
    submission_file = submission_dir / "anonymized.csv"
    
    # 1. Leer los datos
    df_raw = pd.read_csv(raw_file)
    df_anon = pd.DataFrame()
    
    # 2. Enmascarar loyalty_card_number (8 asteriscos + últimos 4 dígitos)
    tarjetas_str = df_raw["loyalty_card_number"].astype(str).str.zfill(12)
    df_anon["loyalty_card_number"] = "********" + tarjetas_str.str[-4:]
    
    # 3. Mantener el annual_spend idéntico
    df_anon["annual_spend"] = df_raw["annual_spend"]
    
    # 4. Generar el customer_id
    df_anon["customer_id"] = df_raw["document_id"].apply(generar_customer_id)
    
    # 5. Agrupar la edad en los rangos permitidos (20-29, 30-39, etc.)
    df_anon["age_group"] = pd.cut(
        df_raw["age"], 
        bins=[20, 30, 40, 50, 60, 70], 
        labels=["20-29", "30-39", "40-49", "50-59", "60-69"], 
        right=False
    )
    
    # 6. Mapear las ciudades a sus respectivas regiones (Andina, Caribe, Pacífica)
    city_to_region = {
        'Envigado': 'Andina', 'Cali': 'Pacífica', 'Bogotá': 'Andina', 
        'Itagüí': 'Andina', 'Medellín': 'Andina', 'Bucaramanga': 'Andina', 
        'Rionegro': 'Andina', 'Cartagena': 'Caribe', 'Pereira': 'Andina', 
        'Bello': 'Andina', 'Barranquilla': 'Caribe', 'Manizales': 'Andina'
    }
    df_anon["region"] = df_raw["city"].map(city_to_region)
    
    # 7. Mapear las ocupaciones a los grupos permitidos
    occ_to_group = {
        'Comerciante': 'Comercio y oficios', 
        'Ingeniero de sistemas': 'Tecnología y diseño', 
        'Docente': 'Salud y educación', 
        'Abogada': 'Servicios profesionales',
        'Diseñadora gráfica': 'Tecnología y diseño', 
        'Médico': 'Salud y educación', 
        'Administradora': 'Servicios profesionales', 
        'Contadora': 'Servicios profesionales', 
        'Enfermera': 'Salud y educación', 
        'Arquitecta': 'Servicios profesionales', 
        'Analista financiera': 'Servicios profesionales', 
        'Técnico electricista': 'Comercio y oficios'
    }
    df_anon["occupation_group"] = df_raw["occupation"].map(occ_to_group)
    
    # 8. Filtrar y ordenar exactamente las columnas que exige el test_02
    columnas_finales = [
        "loyalty_card_number",
        "annual_spend",
        "customer_id",
        "age_group",
        "region",
        "occupation_group"
    ]
    df_anon = df_anon[columnas_finales]
    
    # 9. Crear el directorio "submission" si no existe y exportar el CSV
    submission_dir.mkdir(parents=True, exist_ok=True)
    df_anon.to_csv(submission_file, index=False)
    print(f"✅ Archivo generado exitosamente en: {submission_file}")

if __name__ == "__main__":
    main()


