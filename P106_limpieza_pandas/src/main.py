import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "ventas.csv"
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "ventas.csv"

EXPECTED_COLUMNS = [
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

SUPPLIER_REPLACEMENTS = {
    "BANCOLOMBIA S.A.": "Bancolombia S.A.",
    "Corona S.A.S.": "Corona SAS",
    "Ecopetrol  S.A.": "Ecopetrol S.A.",
    "GOOGLE COLOMBIA LTDA.": "Google Colombia Ltda.",
    "Grupo  Éxito  S.A.": "Grupo Éxito S.A.",
}

COUNTRY_REPLACEMENTS = {
    "COL": "COL",
    "CO": "COL",
    "COLOMBIA": "COL",
}

VALID_CITIES = {
    "bogota": "Bogotá",
    "medellin": "Medellín",
    "sopo": "Sopó",
    "tenjo": "Tenjo",
}

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%B %d, %Y",
    "%b %d, %Y",
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def collapse_spaces(text):
    """Quita espacios al inicio/final y colapsa espacios repetidos."""
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def fold(text):
    """Minúsculas, sin tildes, sin signos y sin espacios repetidos."""
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return collapse_spaces(text)


def read_input():
    """Lee el CSV como texto (para no perder ceros ni mezclar tipos)."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(INPUT_FILE, dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {INPUT_FILE} con utf-8 ni latin-1")


# ---------------------------------------------------------------------------
# Limpieza por columna
# ---------------------------------------------------------------------------
def clean_column_names(df):
    # Casos tipicos en la columna
    # ' Supplier ID ' -> "supplier_id"
    # 'City ' -> "city"
    # 'Purchase Date' -> "purchase_date"
    df.columns = (
        df.columns.str.replace("\ufeff", "", regex=False)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    return df


def clean_supplier_column(df):
    lookup = {fold(key): value for key, value in SUPPLIER_REPLACEMENTS.items()}

    supplier = df["supplier"].astype("string").str.replace(r"\s+", " ", regex=True)
    supplier = supplier.str.strip()

    # Se compara sin importar mayúsculas, tildes ni espacios repetidos.
    folded = supplier.map(lambda v: fold(v) if pd.notna(v) else v)
    replacement = folded.map(lookup)
    df["supplier"] = replacement.fillna(supplier)
    return df


def clean_country_column(df):
    country = df["country"].astype("string").map(
        lambda v: collapse_spaces(v).upper().replace(".", "") if pd.notna(v) else v
    )
    country = country.map(lambda v: strip_accents(v) if pd.notna(v) else v)
    df["country"] = country.map(COUNTRY_REPLACEMENTS).fillna(country)
    return df


def _normalize_city(value):
    if pd.isna(value):
        return value
    key = fold(value)
    if not key:
        return pd.NA
    # Coincidencia exacta o que empiece igual ("bogota d c" -> "bogota")
    for city_key, city_name in VALID_CITIES.items():
        if key == city_key or key.startswith(city_key + " "):
            return city_name
    # Errores de digitación ("medelin", "bogta", ...)
    close = get_close_matches(key, list(VALID_CITIES), n=1, cutoff=0.7)
    if close:
        return VALID_CITIES[close[0]]
    return collapse_spaces(value)


def clean_city_column(df):
    df["city"] = df["city"].astype("string").map(_normalize_city)
    return df


def _parse_date(value):
    if pd.isna(value):
        return pd.NaT
    text = collapse_spaces(str(value))
    # Si trae hora ("2024-03-05 10:30:00" o "2024-03-05T10:30:00"), se ignora.
    iso = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[ T].*)?$", text)
    if iso:
        text = iso.group(1)
    for date_format in DATE_FORMATS:
        try:
            return pd.Timestamp(pd.to_datetime(text, format=date_format))
        except (ValueError, TypeError):
            continue
    return pd.NaT


def clean_purchase_date_column(df):
    parsed = df["purchase_date"].map(_parse_date)
    df["purchase_date"] = pd.to_datetime(parsed).dt.strftime("%Y-%m-%d")
    return df


def _to_number(value):
    """Convierte '$1.200.000,50', '1,200.50', '15%', ' 3 ' en float."""
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    if not text:
        return float("nan")
    text = re.sub(r"[^\d,.\-]", "", text)
    if not re.search(r"\d", text):
        return float("nan")

    has_comma, has_dot = "," in text, "." in text
    if has_comma and has_dot:
        # El último separador es el decimal, el otro es de miles.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", text):
            text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
    elif has_dot and text.count(".") > 1:
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return float("nan")


def clean_numeric_columns(df):
    for column in ["amount", "unit_price"]:
        df[column] = df[column].map(_to_number)

    # Unidades: enteros (se deja nulo si no hay dato)
    df["units"] = df["units"].map(_to_number).round().astype("Int64")

    # Peso: no puede ser negativo
    weight = df["weight"].map(_to_number)
    df["weight"] = weight.where(weight.isna() | (weight >= 0))

    # Descuento: debe quedar entre 0 y 1 (15 o "15%" -> 0.15)
    discount = df["discount"].map(_to_number)
    discount = discount.where(discount <= 1, discount / 100)
    df["discount"] = discount.where(discount.between(0, 1))
    return df


def clean_email_column(df):
    df["contact_email"] = (
        df["contact_email"].astype("string").str.strip().str.lower()
    )
    return df


def main():
    df = read_input()
    df = clean_column_names(df)
    df = clean_supplier_column(df)
    df = clean_country_column(df)
    df = clean_city_column(df)
    df = clean_purchase_date_column(df)
    df = clean_numeric_columns(df)
    df = clean_email_column(df)

    df = df[EXPECTED_COLUMNS]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()

