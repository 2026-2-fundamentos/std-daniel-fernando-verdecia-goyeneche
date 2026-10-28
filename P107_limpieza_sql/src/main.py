"""P107 - Limpieza de datos de ventas.

Lee los datos sucios (SQLite o CSV dentro de esta carpeta), los limpia y
genera submission/ventas.csv con las columnas que pide el test.
"""

import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "ventas.csv"

COLUMNS = [
    "supplier_id",
    "supplier",
    "country",
    "city",
    "purchase_date",
    "amount",
    "discount",
    "weight",
    "units",
    "unit_price",
    "contact_email",
]

# Si las columnas originales tienen otro nombre, ajústalo aquí
# (clave = nombre original en minúsculas, valor = nombre esperado).
RENAME = {
    "id_proveedor": "supplier_id",
    "supplier id": "supplier_id",  # <-- Nueva
    "proveedor": "supplier",
    "pais": "country",
    "país": "country",
    "ciudad": "city",
    "fecha_compra": "purchase_date",
    "fecha": "purchase_date",
    "purchase date": "purchase_date",  # <-- Nueva
    "monto": "amount",
    "valor": "amount",
    "descuento": "discount",
    "peso": "weight",
    "unidades": "units",
    "cantidad": "units",
    "precio_unitario": "unit_price",
    "unit price": "unit_price",  # <-- Nueva
    "correo": "contact_email",
    "email": "contact_email",
    "contact email": "contact_email",  # <-- Nueva
}

COUNTRY_MAP = {"col": "COL", "co": "COL", "colombia": "COL"}
CITY_MAP = {
    "bogota": "Bogotá",
    "bogota dc": "Bogotá",
    "santa fe de bogota": "Bogotá",
    "medellin": "Medellín",
    "sopo": "Sopó",
    "tenjo": "Tenjo",
}


def load_raw() -> pd.DataFrame:
    """Carga los datos originales desde una base SQLite o un CSV de la carpeta."""
    dbs = [p for p in ACTIVITY_DIR.rglob("*") if p.suffix in {".db", ".sqlite", ".sqlite3"}]
    if dbs:
        with sqlite3.connect(dbs[0]) as con:
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type = 'table'", con
            )["name"].tolist()
            return pd.read_sql(f'SELECT * FROM "{tables[0]}"', con)

    csvs = [
        p
        for p in ACTIVITY_DIR.rglob("*.csv")
        if "submission" not in p.parts and "tests" not in p.parts
    ]
    if csvs:
        return pd.read_csv(csvs[0], dtype=str)

    raise FileNotFoundError(f"No encontré datos de entrada (.db/.sqlite/.csv) en {ACTIVITY_DIR}")


def text_key(value) -> str | None:
    """minúsculas, sin tildes, sin puntuación y con espacios simples."""
    if pd.isna(value):
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^a-z ]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_number(text, money: bool):
    if text is None or pd.isna(text) or text in ("", "-"):
        return None
    if "," in text and "." in text:
        # el último separador es el decimal: '1.200,50' o '1,200.50'
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".") if text.count(",") == 1 else text.replace(",", "")
    elif "." in text:
        # '2.500.000' o (en columnas de dinero) '85.000' -> separador de miles
        if text.count(".") > 1 or (money and re.fullmatch(r"-?\d{1,3}\.\d{3}", text)):
            text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def to_number(series: pd.Series, money: bool = False) -> pd.Series:
    """Convierte textos como '$1.200,50', '15%' o '3 kg' a número."""
    s = series.astype("string").str.strip().str.replace(r"[^\d,.\-]", "", regex=True)
    return pd.to_numeric(s.map(lambda v: _parse_number(v, money)), errors="coerce")


def parse_dates(series: pd.Series) -> pd.Series:
    """Acepta ISO (2024-04-02) y día/mes/año (02/04/2024) y devuelve YYYY-MM-DD."""
    s = series.astype("string").str.strip()
    iso = pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")
    rest = s.where(iso.isna())
    try:
        other = pd.to_datetime(rest, errors="coerce", dayfirst=True, format="mixed")
    except (TypeError, ValueError):  # pandas < 2.0
        other = pd.to_datetime(rest, errors="coerce", dayfirst=True)
    return iso.fillna(other).dt.strftime("%Y-%m-%d")


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.rename(columns=RENAME)

    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Faltan columnas {missing}. Columnas encontradas: {list(df.columns)}")
    df = df[COLUMNS]

    # supplier: sin espacios al inicio/final ni espacios dobles
    df["supplier"] = df["supplier"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)

    # country -> 'COL'
    df["country"] = df["country"].map(lambda v: COUNTRY_MAP.get(text_key(v)))

    # city -> nombre canónico
    df["city"] = df["city"].map(lambda v: CITY_MAP.get(text_key(v)))

    # purchase_date -> YYYY-MM-DD
    df["purchase_date"] = parse_dates(df["purchase_date"])

    # numéricos
    df["amount"] = to_number(df["amount"], money=True)
    df["unit_price"] = to_number(df["unit_price"], money=True)
    df["units"] = to_number(df["units"]).round().astype("Int64")

    # discount entre 0 y 1 (si viene como 15 o '15%', se pasa a 0.15)
    discount = to_number(df["discount"])
    discount = discount.where(discount <= 1, discount / 100)
    df["discount"] = discount.where(discount.between(0, 1))

    # weight >= 0 (los negativos son errores -> vacío)
    weight = to_number(df["weight"])
    df["weight"] = weight.where(weight >= 0)

    df["contact_email"] = df["contact_email"].astype("string").str.strip().str.lower()

    # El test exige estos campos válidos en todas las filas
    df = df.dropna(subset=["supplier", "country", "city", "purchase_date"])
    return df.drop_duplicates().reset_index(drop=True)


def main():
    sales = clean(load_raw())
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sales.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"{len(sales)} filas guardadas en {OUTPUT_FILE}")


if __name__ == "__main__":
    print("Iniciando el script...")
    try:
        main()
        print("Script finalizado exitosamente.")
    except Exception as e:
        print(f"¡Ocurrió un error!: {type(e).__name__} - {e}")



