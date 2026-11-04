import json
import re
from pathlib import Path
import pandas as pd

def main():
    columnas_requeridas = [
        "supplier_id", "supplier", "country", "city", "purchase_date",
        "amount", "discount", "weight", "units", "unit_price", "contact_email"
    ]
    
    df = pd.read_csv("data/ventas.csv.gz", dtype=str, na_filter=False, encoding="utf-8")
    
    df.columns = [c.replace('\ufeff', '').strip().lower().replace(' ', '_') for c in df.columns]
    
    missing_required = sorted(list(set(columnas_requeridas) - set(df.columns)))
    unexpected = sorted(list(set(df.columns) - set(columnas_requeridas)))
    
    missings = {}
    for col in df.columns:
        missings[col] = int(df[col].isin(['', 'N/A']).sum())
        
    invalid_emails = 0
    if 'contact_email' in df.columns:
        patron = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
        for val in df['contact_email']:
            if val not in ['', 'N/A']:
                if not patron.match(val):
                    invalid_emails += 1
                    
    invalid_units = 0
    if 'units' in df.columns:
        for val in df['units']:
            if val not in ['', 'N/A']:
                try:
                    num = float(val)
                    if num <= 0 or not num.is_integer():
                        invalid_units += 1
                except ValueError:
                    invalid_units += 1
                    
    paises = sorted(df['country'].unique().tolist()) if 'country' in df.columns else []
    
    reporte = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_required_columns": missing_required,
        "unexpected_columns": unexpected,
        "duplicate_row_count": int(df.duplicated().sum()),
        "duplicate_supplier_id_row_count": int(df.duplicated(subset=['supplier_id'], keep=False).sum()) if 'supplier_id' in df.columns else 0,
        "missing_value_count_by_column": missings,
        "invalid_email_count": invalid_emails,
        "invalid_unit_count": invalid_units,
        "country_values": paises
    }
    
    ruta_salida = Path("submission")
    ruta_salida.mkdir(parents=True, exist_ok=True)
    
    with open(ruta_salida / "data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=4)
        
    return reporte

if __name__ == "__main__":
    main()