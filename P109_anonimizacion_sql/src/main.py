import hashlib
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_FILE = BASE_DIR / "data" / "raw.csv"
OUTPUT_FILE = BASE_DIR / "submission" / "anonymized.csv"


SALT = "k7Qx9vLw2Zp4"

REGIONS = {
    "Medellín": "Andina",
    "Bogotá": "Andina",
    "Itagüí": "Andina",
    "Bello": "Andina",
    "Envigado": "Andina",
    "Rionegro": "Andina",
    "Pereira": "Andina",
    "Manizales": "Andina",
    "Bucaramanga": "Andina",
    "Cartagena": "Caribe",
    "Barranquilla": "Caribe",
    "Cali": "Pacífica",
}

OCCUPATION_GROUPS = {
    "Comerciante": "Comercio y oficios",
    "Técnico electricista": "Comercio y oficios",
    "Docente": "Salud y educación",
    "Enfermera": "Salud y educación",
    "Médico": "Salud y educación",
    "Administradora": "Servicios profesionales",
    "Contadora": "Servicios profesionales",
    "Analista financiera": "Servicios profesionales",
    "Abogada": "Servicios profesionales",
    "Arquitecta": "Servicios profesionales",
    "Ingeniero de sistemas": "Tecnología y diseño",
    "Diseñadora gráfica": "Tecnología y diseño",
}


def mask_card(card):
    return "********" + str(card).zfill(12)[-4:]


def make_customer_id(document_id):
    digest = hashlib.sha256(f"{SALT}{document_id}".encode()).hexdigest()
    return "CUST-" + digest[:12].upper()


def age_group(age):
    start = age // 10 * 10
    return f"{start}-{start + 9}"


def main():
    raw = pd.read_csv(RAW_FILE)

    anonymized = pd.DataFrame(
        {
            "loyalty_card_number": raw["loyalty_card_number"].apply(mask_card),
            "annual_spend": raw["annual_spend"],
            "customer_id": raw["document_id"].apply(make_customer_id),
            "age_group": raw["age"].apply(age_group),
            "region": raw["city"].map(REGIONS),
            "occupation_group": raw["occupation"].map(OCCUPATION_GROUPS),
        }
    )

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    anonymized.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()