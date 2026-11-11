from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "superstore_orders.csv.gz"
SUBMISSION_DIR = BASE_DIR / "submission"

DISCOUNT_BINS = [-np.inf, 0, 0.05, 0.10, np.inf]
DISCOUNT_LABELS = ["0%", "1%-5%", "6%-10%", "más de 10%"]


def _agregar(grupos) -> pd.DataFrame:
    return grupos.agg(
        lines=("Order ID", "size"),
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        loss_lines=("is_loss", "sum"),
        lost_profit=("loss", "sum"),
    )


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Intenta leer usando tabulador o punto y coma, que evitan el ParserError original
    try:
        df = pd.read_csv(DATA_PATH, sep="\t")
        if "Profit" not in df.columns:
            df = pd.read_csv(DATA_PATH, sep=";")
    except Exception:
        df = pd.read_csv(DATA_PATH)
        
    # CORRECCIÓN: Si Pandas leyó las columnas numéricas como texto por tener comas decimales,
    # reemplazamos la coma por punto y convertimos a float para poder operar.
    for col in ["Sales", "Profit", "Discount"]:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(",", ".").astype(float)

    # Ahora esto funcionará porque 'Profit' ya es un número (float), no un texto
    df["is_loss"] = df["Profit"] < 0
    df["loss"] = np.where(df["is_loss"], -df["Profit"], 0.0)
    df["discount_band"] = pd.cut(
        df["Discount"].round(4),
        bins=DISCOUNT_BINS,
        labels=DISCOUNT_LABELS,
    )

    lines = len(df)
    sales = df["Sales"].sum()
    profit = df["Profit"].sum()
    loss_lines = int(df["is_loss"].sum())

    summary = pd.DataFrame([{
        "lines": lines,
        "orders": df["Order ID"].nunique(),
        "sales": sales,
        "profit": profit,
        "profit_margin": profit / sales,
        "loss_lines": loss_lines,
        "loss_line_rate": loss_lines / lines,
        "lost_profit": df["loss"].sum(),
    }]).round(4)

    discounts = _agregar(df.groupby("discount_band", observed=False)).reset_index()
    discounts = discounts.assign(
        discount_band=lambda x: x["discount_band"].astype(str),
        profit_margin=lambda x: x["profit"] / x["sales"],
        loss_line_rate=lambda x: x["loss_lines"] / x["lines"]
    )[["discount_band", "lines", "sales", "profit", "profit_margin", "loss_line_rate", "lost_profit"]].round(4)

    segments = _agregar(df.groupby(["Customer Segment", "Product Category"])).reset_index()
    segments = segments.assign(
        profit_margin=lambda x: x["profit"] / x["sales"]
    )
    segments = (
        segments[segments["lines"] >= 100]
        .sort_values("lost_profit", ascending=False)
        .head(5)
        [["Customer Segment", "Product Category", "lines", "sales", "profit", "profit_margin", "lost_profit"]]
        .round(4)
    )

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUBMISSION_DIR / "profitability_summary.csv", index=False)
    discounts.to_csv(SUBMISSION_DIR / "discount_summary.csv", index=False)
    segments.to_csv(SUBMISSION_DIR / "priority_segments.csv", index=False)

    return summary, discounts, segments