import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler

RANDOM_STATE = 42
TARGET = "MPG"
NUMERIC_FEATURES = [
    "Cylinders",
    "Displacement",
    "Horsepower",
    "Weight",
    "Acceleration",
    "Model Year",
]
CATEGORICAL_FEATURES = ["Origin"]


def find_activity_dir():
    here = Path(__file__).resolve().parent
    for folder in [here, *here.parents]:
        if (folder / "tests").is_dir():
            return folder
    for test_file in here.glob("*/tests/test_*.py"):
        return test_file.parents[1]
    for test_file in here.parent.glob("*/tests/test_*.py"):
        return test_file.parents[1]
    return here


ACTIVITY_DIR = find_activity_dir()
SUBMISSION_DIR = ACTIVITY_DIR / "submission"
SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)


def find_data_file():
    here = Path(__file__).resolve().parent
    search_roots = [ACTIVITY_DIR, here, ACTIVITY_DIR.parent]
    for root in search_roots:
        for relative in ["auto_mpg.csv", "data/auto_mpg.csv", "submission/auto_mpg.csv"]:
            candidate = root / relative
            if candidate.is_file():
                return candidate
    for root in search_roots:
        matches = list(root.rglob("auto_mpg.csv"))
        if matches:
            return matches[0]
    raise FileNotFoundError("auto_mpg.csv no encontrado")


def load_data():
    df = pd.read_csv(find_data_file())
    df.columns = [column.strip() for column in df.columns]
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df[TARGET].copy()
    return X, y


def build_features_preprocessor():
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_flexible_features_preprocessor():
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=2, include_bias=False)),
            ("scaler_poly", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def evaluate(name, model, X_train, X_test, y_train, y_test):
    cv_scores = cross_val_score(
        model, X_train, y_train, cv=5, scoring="neg_root_mean_squared_error"
    )
    model.fit(X_train, y_train)
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    return {
        "model": name,
        "cv_rmse": float(-cv_scores.mean()),
        "train_rmse": float(np.sqrt(mean_squared_error(y_train, train_pred))),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, test_pred))),
        "test_mae": float(mean_absolute_error(y_test, test_pred)),
        "test_r2": float(r2_score(y_test, test_pred)),
    }


def save_pickle(obj, filename):
    with open(SUBMISSION_DIR / filename, "wb") as file:
        pickle.dump(obj, file)


def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    features_preprocessor = build_features_preprocessor()
    flexible_features_preprocessor = build_flexible_features_preprocessor()

    features_preprocessor.fit(X_train)
    flexible_features_preprocessor.fit(X_train)

    linear_model = Pipeline(
        steps=[
            ("preprocessor", build_features_preprocessor()),
            ("regressor", LinearRegression()),
        ]
    )

    linear_flexible_model = Pipeline(
        steps=[
            ("preprocessor", build_flexible_features_preprocessor()),
            ("regressor", Ridge(alpha=10.0, random_state=RANDOM_STATE)),
        ]
    )

    mlp = Pipeline(
        steps=[
            ("preprocessor", build_features_preprocessor()),
            (
                "regressor",
                MLPRegressor(
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    solver="adam",
                    alpha=1e-3,
                    learning_rate_init=1e-3,
                    max_iter=2000,
                    early_stopping=True,
                    validation_fraction=0.15,
                    n_iter_no_change=30,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    results = [
        evaluate("linear_model", linear_model, X_train, X_test, y_train, y_test),
        evaluate(
            "linear_flexible_model",
            linear_flexible_model,
            X_train,
            X_test,
            y_train,
            y_test,
        ),
        evaluate("mlp", mlp, X_train, X_test, y_train, y_test),
    ]

    comparison = pd.DataFrame(results).sort_values("test_rmse").reset_index(drop=True)
    comparison.to_csv(SUBMISSION_DIR / "model_comparison.csv", index=False)

    save_pickle(features_preprocessor, "features_preprocessor.pkl")
    save_pickle(flexible_features_preprocessor, "flexible_features_preprocessor.pkl")
    save_pickle(linear_flexible_model, "linear_flexible_model.pkl")
    save_pickle(mlp, "mlp.pkl")

    print(comparison.to_string(index=False))
    print()
    print("Archivos guardados en:", SUBMISSION_DIR)


if __name__ == "__main__":
    main()