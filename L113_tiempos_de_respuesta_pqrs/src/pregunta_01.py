import os
import numpy as np
import pandas as pd

def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_web = pd.read_csv("data/historical_requests_web.csv.gz")
    df_web["channel"] = "web"
    
    df_letter = pd.read_csv("data/historical_requests_letter.csv.gz")
    df_letter["channel"] = "letter"
    
    df = pd.concat([df_letter, df_web], ignore_index=True)
    df = df.drop_duplicates()
    
    df["in_date"] = pd.to_datetime(df["in_date"])
    df["out_date"] = pd.to_datetime(df["out_date"])
    
    answered = df["out_date"].notna()
    
    df["calendar_days"] = np.nan
    df.loc[answered, "calendar_days"] = (df.loc[answered, "out_date"] - df.loc[answered, "in_date"]).dt.days
    
    in_d = df.loc[answered, "in_date"].values.astype("datetime64[D]")
    out_d = df.loc[answered, "out_date"].values.astype("datetime64[D]")
    
    b_days = np.busday_count(in_d + np.timedelta64(1, "D"), out_d + np.timedelta64(1, "D"))
    df["business_days"] = np.nan
    df.loc[answered, "business_days"] = b_days
    
    df["on_time"] = 0
    df.loc[answered, "on_time"] = (df.loc[answered, "business_days"] <= 15).astype(int)
    
    channel_summary = df.groupby("channel").agg(
        requests=("channel", "size"),
        answered=("out_date", "count"),
        median_business_days=("business_days", "median"),
        on_time_rate=("on_time", "mean")
    ).reset_index()
    channel_summary.insert(3, "pending", channel_summary["requests"] - channel_summary["answered"])
    
    df["year"] = df["in_date"].dt.year
    yearly_summary = df.groupby(["year", "channel"]).agg(
        requests=("channel", "size"),
        answered=("out_date", "count"),
        on_time_rate=("on_time", "mean")
    ).reset_index()
    yearly_summary.insert(3, "pending", yearly_summary["requests"] - yearly_summary["answered"])
    yearly_summary = yearly_summary.drop(columns=["answered"])
    yearly_summary = yearly_summary.sort_values(["year", "channel"])
    
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["day_name"] = pd.Categorical(df["day_name"], categories=day_order, ordered=True)
    
    entry_day_summary = df.groupby("day_name", observed=False).agg(
        requests=("channel", "size"),
        median_calendar_days=("calendar_days", "median"),
        median_business_days=("business_days", "median")
    ).reset_index()
    
    os.makedirs("submission", exist_ok=True)
    
    channel_summary = channel_summary[["channel", "requests", "answered", "pending", "median_business_days", "on_time_rate"]]
    channel_summary.to_csv("submission/channel_summary.csv", index=False)
    
    yearly_summary = yearly_summary[["year", "channel", "requests", "pending", "on_time_rate"]]
    yearly_summary.to_csv("submission/yearly_summary.csv", index=False)
    
    entry_day_summary = entry_day_summary[["day_name", "requests", "median_calendar_days", "median_business_days"]]
    entry_day_summary.to_csv("submission/entry_day_summary.csv", index=False)
    
    return channel_summary, yearly_summary, entry_day_summary