import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def build_cohort_analysis() -> pd.DataFrame:
    df = pd.read_csv("data/sales.csv.gz")
    
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["order_month"] = df["OrderDate"].dt.to_period("M")
    df["cohort"] = df.groupby("CustomerID")["order_month"].transform("min")
    
    df["period_index"] = (
        (df["order_month"].dt.year - df["cohort"].dt.year) * 12
        + (df["order_month"].dt.month - df["cohort"].dt.month)
    )
    
    df["cohort_month"] = df["cohort"].astype(str)
    
    cohort_data = df.groupby(["cohort_month", "period_index"])["CustomerID"].nunique().reset_index()
    cohort_data.rename(columns={"CustomerID": "active_customers"}, inplace=True)
    
    cohort_sizes = cohort_data[cohort_data["period_index"] == 0][["cohort_month", "active_customers"]].copy()
    cohort_sizes.rename(columns={"active_customers": "cohort_size"}, inplace=True)
    
    cohort_data = cohort_data.merge(cohort_sizes, on="cohort_month")
    cohort_data["retention_rate"] = cohort_data["active_customers"] / cohort_data["cohort_size"]
    
    cohort_data = cohort_data[
        ["cohort_month", "period_index", "active_customers", "cohort_size", "retention_rate"]
    ].sort_values(["cohort_month", "period_index"])
    
    os.makedirs("submission", exist_ok=True)
    cohort_data.to_csv("submission/cohort_retention.csv", index=False)
    
    pivot = cohort_data.pivot(index="cohort_month", columns="period_index", values="retention_rate")
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt=".1%", cmap="Blues")
    plt.tight_layout()
    plt.savefig("submission/cohort_retention_heatmap.png")
    plt.close()
    
    return cohort_data