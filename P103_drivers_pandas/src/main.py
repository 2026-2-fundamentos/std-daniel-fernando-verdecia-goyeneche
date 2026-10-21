import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd


def find_project_dir():
    if "__file__" in globals():
        folder = os.path.dirname(os.path.abspath(__file__))
    else:
        folder = os.getcwd()
    while not os.path.isfile(os.path.join(folder, "data", "drivers.csv")):
        parent = os.path.dirname(folder)
        if parent == folder:
            raise FileNotFoundError("No se encontró la carpeta data con drivers.csv")
        folder = parent
    return folder


project_dir = find_project_dir()
data_dir = os.path.join(project_dir, "data")
submission_dir = os.path.join(project_dir, "submission")
os.makedirs(submission_dir, exist_ok=True)


drivers = pd.read_csv(
    os.path.join(data_dir, "drivers.csv"),
    sep=",",
    thousands=None,
    decimal=".",
)

timesheet = pd.read_csv(
    os.path.join(data_dir, "timesheet.csv"),
    sep=",",
    thousands=None,
    decimal=".",
)


mean_timesheet = timesheet.groupby("driverId")[["hours-logged", "miles-logged"]].mean()

group_means = timesheet.groupby("driverId")[["hours-logged", "miles-logged"]].transform("mean")
below_mean = timesheet[
    (timesheet["hours-logged"] < group_means["hours-logged"])
    & (timesheet["miles-logged"] < group_means["miles-logged"])
]

sum_timesheet = timesheet.groupby("driverId", as_index=False)[
    ["hours-logged", "miles-logged"]
].sum()

hours_range = timesheet.groupby("driverId")["hours-logged"].agg(["min", "max"])

summary = pd.merge(
    sum_timesheet,
    drivers[["driverId", "name"]],
    on="driverId",
)

summary.to_csv(
    os.path.join(submission_dir, "summary.csv"),
    sep=",",
    header=True,
    index=False,
)

top10 = summary.sort_values(by="miles-logged", ascending=False).head(10)
top10 = top10.set_index("name")

top10["miles-logged"].plot.barh(color="tab:orange", alpha=0.6)

plt.gca().invert_yaxis()

plt.gca().get_xaxis().set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ","))
)

plt.xticks(rotation=90)

plt.gca().spines["left"].set_color("lightgray")
plt.gca().spines["bottom"].set_color("gray")
plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.savefig(os.path.join(submission_dir, "top10_drivers.png"), bbox_inches="tight")

print("Resultados guardados en", submission_dir)