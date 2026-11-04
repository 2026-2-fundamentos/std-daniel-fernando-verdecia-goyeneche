import json
import os
import numpy as np
import pandas as pd


def pregunta_01():
    df = pd.read_csv("data/insurance.csv.gz")

    orig_qis = ["age", "sex", "bmi", "children", "region"]
    orig_sizes = df.groupby(orig_qis).size()
    original_k = int(orig_sizes.min())
    original_unique_records = int((orig_sizes == 1).sum())

    conditions_age = [
        df["age"] <= 29,
        (df["age"] >= 30) & (df["age"] <= 39),
        (df["age"] >= 40) & (df["age"] <= 49),
        df["age"] >= 50,
    ]
    choices_age = ["18-29", "30-39", "40-49", "50-64"]
    df["age_group"] = np.select(conditions_age, choices_age)

    conditions_bmi = [
        df["bmi"] < 18.5,
        (df["bmi"] >= 18.5) & (df["bmi"] < 25),
        (df["bmi"] >= 25) & (df["bmi"] < 30),
        df["bmi"] >= 30,
    ]
    choices_bmi = ["bajo peso", "normal", "sobrepeso", "obesidad"]
    df["bmi_group"] = np.select(conditions_bmi, choices_bmi)

    conditions_children = [
        df["children"] == 0,
        (df["children"] >= 1) & (df["children"] <= 2),
        df["children"] >= 3,
    ]
    choices_children = ["0", "1-2", "3+"]
    df["children_group"] = np.select(conditions_children, choices_children)

    def eval_scheme(qis):
        sizes = df.groupby(qis).size()
        row_sizes = df.groupby(qis)["age"].transform("size")
        published_mask = row_sizes >= 5
        pub_df = df[published_mask]

        smoker_uniques = (
            pub_df.groupby(qis)["smoker"].nunique().reset_index(name="nunique")
        )
        non_diverse = smoker_uniques[smoker_uniques["nunique"] == 1].drop(
            columns="nunique"
        )

        classes_no_div = len(non_diverse)
        if classes_no_div > 0:
            records_no_div = len(pd.merge(pub_df, non_diverse, on=qis, how="inner"))
        else:
            records_no_div = 0

        return {
            "quasi_identifiers": qis,
            "equivalence_classes": int(len(sizes)),
            "k_before_suppression": int(sizes.min()),
            "suppressed_records": int((~published_mask).sum()),
            "published_records": int(published_mask.sum()),
            "published_classes": int((sizes >= 5).sum()),
            "classes_without_smoker_diversity": int(classes_no_div),
            "records_without_smoker_diversity": int(records_no_div),
        }

    scheme_1 = ["age_group", "sex", "bmi_group", "children_group", "region"]
    scheme_2 = ["age_group", "sex", "bmi_group", "region"]

    res_1 = eval_scheme(scheme_1)
    res_2 = eval_scheme(scheme_2)

    if res_1["suppressed_records"] < res_2["suppressed_records"]:
        selected = "with_children"
        sel_qis = scheme_1
    else:
        selected = "without_children"
        sel_qis = scheme_2

    row_sizes_sel = df.groupby(sel_qis)["age"].transform("size")
    published_df = df[row_sizes_sel >= 5].copy()

    report = {
        "original_k": original_k,
        "original_unique_records": original_unique_records,
        "schemes": {"with_children": res_1, "without_children": res_2},
        "selected_scheme": selected,
        "mean_charges_original": float(df["charges"].mean()),
        "mean_charges_published": float(published_df["charges"].mean()),
        "smoker_rate_original": float((df["smoker"] == "yes").mean()),
        "smoker_rate_published": float((published_df["smoker"] == "yes").mean()),
    }

    os.makedirs("submission", exist_ok=True)
    with open("submission/privacy_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    cols_to_publish = sel_qis + ["smoker", "charges"]
    published_df[cols_to_publish].to_csv(
        "submission/insurance_published.csv", index=False
    )

    return report