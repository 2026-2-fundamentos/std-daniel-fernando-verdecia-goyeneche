import glob
import os
import pandas as pd


def clean_campaign_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = sorted(glob.glob("data/*.csv.gz"))
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    if "client_id" not in df.columns:
        if "Unnamed: 0" in df.columns:
            df["client_id"] = df["Unnamed: 0"]
        else:
            df["client_id"] = df.index

    df = df.rename(
        columns={
            "default": "credit_default",
            "housing": "mortgage",
            "campaign": "number_contacts",
            "duration": "contact_duration",
            "previous": "previous_campaign_contacts",
            "poutcome": "previous_outcome",
            "y": "campaign_outcome",
            "cons.price.idx": "cons_price_idx",
            "euribor3m": "euribor_three_months",
        }
    )

    df = df.sort_values("client_id").reset_index(drop=True)

    client = df[
        [
            "client_id",
            "age",
            "job",
            "marital",
            "education",
            "credit_default",
            "mortgage",
        ]
    ].copy()

    client["job"] = (
        client["job"]
        .str.replace(".", "", regex=False)
        .str.replace("-", "_", regex=False)
    )
    client["education"] = (
        client["education"]
        .str.replace(".", "_", regex=False)
        .replace("unknown", pd.NA)
    )
    client["credit_default"] = (client["credit_default"] == "yes").astype(int)
    client["mortgage"] = (client["mortgage"] == "yes").astype(int)

    month_map = {
        "jan": "01",
        "feb": "02",
        "mar": "03",
        "apr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "aug": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dec": "12",
    }

    month_str = (
        df["month"]
        .astype(str)
        .str.lower()
        .map(month_map)
        .fillna(df["month"].astype(str).str.zfill(2))
    )
    day_str = df["day"].astype(str).str.zfill(2)
    last_contact_date = "2022-" + month_str + "-" + day_str

    campaign = pd.DataFrame(
        {
            "client_id": df["client_id"],
            "number_contacts": df["number_contacts"],
            "contact_duration": df["contact_duration"],
            "previous_campaign_contacts": df["previous_campaign_contacts"],
            "previous_outcome": (df["previous_outcome"] == "success").astype(int),
            "campaign_outcome": (df["campaign_outcome"] == "yes").astype(int),
            "last_contact_date": last_contact_date,
        }
    )

    economics = df[["client_id", "cons_price_idx", "euribor_three_months"]].copy()

    os.makedirs("submission", exist_ok=True)
    client.to_csv("submission/client.csv", index=False)
    campaign.to_csv("submission/campaign.csv", index=False)
    economics.to_csv("submission/economics.csv", index=False)

    return client, campaign, economics