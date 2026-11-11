import os
import pandas as pd

def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv("data/flights_by_carrier_day_hour.csv.gz")

    hourly = df.groupby("scheduled_departure_hour", as_index=False)[
        ["operated_flights", "delayed_departure_15_flights"]
    ].sum()
    
    hourly["delay_rate"] = hourly["delayed_departure_15_flights"] / hourly["operated_flights"]

    rate_map = hourly.set_index("scheduled_departure_hour")["delay_rate"]
    df["expected_delayed_flights"] = df["operated_flights"] * df["scheduled_departure_hour"].map(rate_map)

    carrier = df.groupby("reporting_airline", as_index=False)[
        ["operated_flights", "delayed_departure_15_flights", "expected_delayed_flights"]
    ].sum()

    carrier = carrier[carrier["operated_flights"] >= 100000].copy()

    carrier["delay_rate"] = carrier["delayed_departure_15_flights"] / carrier["operated_flights"]
    carrier["observed_to_expected_ratio"] = (
        carrier["delayed_departure_15_flights"] / carrier["expected_delayed_flights"]
    )

    carrier["crude_rank"] = carrier["delay_rate"].rank(ascending=False).astype(int)
    carrier["adjusted_rank"] = carrier["observed_to_expected_ratio"].rank(ascending=False).astype(int)

    carrier = carrier.sort_values("adjusted_rank")

    carrier = carrier[
        [
            "reporting_airline",
            "operated_flights",
            "delayed_departure_15_flights",
            "delay_rate",
            "expected_delayed_flights",
            "observed_to_expected_ratio",
            "crude_rank",
            "adjusted_rank",
        ]
    ]

    os.makedirs("submission", exist_ok=True)
    hourly.to_csv("submission/hourly_delay_rates.csv", index=False)
    carrier.to_csv("submission/carrier_adjusted_delays.csv", index=False)

    return hourly, carrier