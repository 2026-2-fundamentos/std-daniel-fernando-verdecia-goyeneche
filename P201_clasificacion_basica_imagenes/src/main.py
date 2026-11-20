import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler

RANDOM_STATE = 42
DATA_FILENAME = "auto_mpg.csv"
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
        for relative in [DATA_FILENAME, f"data/{DATA_FILENAME}", f"submission/{DATA_FILENAME}"]:
            candidate = root / relative
            if candidate.is_file():
                return candidate
    for root in search_roots:
        matches = list(root.rglob(DATA_FILENAME))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"{DATA_FILENAME} no encontrado")


def load_data():
    df = pd.read_csv(find_data_file())
    df.columns = [column.strip() for column in df.columns]
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df[TARGET].copy()
    return X, y


def build_pipeline():
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
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", Ridge(random_state=RANDOM_STATE)),
        ]
    )


def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    param_grid = {
        "preprocessor__num__poly__degree": [1, 2, 3],
        "regressor__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
    }

    estimator = GridSearchCV(
        estimator=build_pipeline(),
        param_grid=param_grid,
        cv=5,
        scoring="neg_root_mean_squared_error",
        refit=True,
        n_jobs=1,
    )
    estimator.fit(X_train, y_train)

    train_pred = estimator.predict(X_train)
    test_pred = estimator.predict(X_test)

    metrics = {
        "best_params": {key: value for key, value in estimator.best_params_.items()},
        "cv_rmse": float(-estimator.best_score_),
        "train_rmse": float(np.sqrt(mean_squared_error(y_train, train_pred))),
        "test_rmse": float(np.sqrt(mean_squared_error(y_test, test_pred))),
        "train_mae": float(mean_absolute_error(y_train, train_pred)),
        "test_mae": float(mean_absolute_error(y_test, test_pred)),
        "train_r2": float(r2_score(y_train, train_pred)),
        "test_r2": float(r2_score(y_test, test_pred)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }

    with open(SUBMISSION_DIR / "estimator.pkl", "wb") as file:
        pickle.dump(estimator, file)

    with open(SUBMISSION_DIR / "metrics.json", "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    print(json.dumps(metrics, indent=4))
    print()
    print("Archivos guardados en:", SUBMISSION_DIR)


if __name__ == "__main__":
    main()