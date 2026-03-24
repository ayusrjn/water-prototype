"""Train sklearn LinearRegression on a CSV (default: /data/input/dataset.csv)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def main() -> None:
    csv_path = Path(os.environ.get("DATA_CSV", "/data/input/dataset.csv"))
    if not csv_path.is_file():
        raise SystemExit(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.shape[1] < 2:
        raise SystemExit("CSV needs at least one feature column and one target column.")

    target_col = os.environ.get("TARGET_COL", df.columns[-1])
    if target_col not in df.columns:
        raise SystemExit(f"Target column not in CSV: {target_col}")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    mse = float(mean_squared_error(y_test, pred))
    r2 = float(r2_score(y_test, pred))

    out = {
        "csv": str(csv_path),
        "target_col": target_col,
        "n_samples": int(len(df)),
        "n_features": int(X.shape[1]),
        "mse": round(mse, 6),
        "r2": round(r2, 6),
        "intercept": float(model.intercept_) if model.intercept_ is not None else None,
        "feature_names": list(X.columns),
        "coefficients": [float(c) for c in model.coef_.ravel()],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
