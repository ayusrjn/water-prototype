"""Train sklearn LogisticRegression on the Iris dataset (or a custom CSV)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def main() -> None:
    # Try to load from CSV, but default to a fallback if it doesn't exist
    csv_path_str = os.environ.get("DATA_CSV", "/data/input/dataset.csv")
    csv_path = Path(csv_path_str)

    if csv_path.is_file():
        df = pd.read_csv(csv_path)
        if df.shape[1] < 2:
            raise SystemExit("CSV needs at least one feature column and one target column.")
            
        target_col = os.environ.get("TARGET_COL", df.columns[-1])
        if target_col not in df.columns:
            raise SystemExit(f"Target column not in CSV: {target_col}")

        X = df.drop(columns=[target_col])
        y = df[target_col]
        dataset_source = str(csv_path)
    else:
        # Fallback to the built-in Iris dataset if no CSV is found
        iris = load_iris(as_frame=True)
        X = iris.data
        y = iris.target
        target_col = "target (iris species)"
        dataset_source = "sklearn.datasets.load_iris"

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Max_iter increased to ensure convergence on the Iris dataset
    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    
    # Classification metrics
    accuracy = float(accuracy_score(y_test, pred))
    f1 = float(f1_score(y_test, pred, average="weighted"))

    out = {
        "dataset_source": dataset_source,
        "target_col": target_col,
        "n_samples": int(len(X)),
        "n_features": int(X.shape[1]),
        "accuracy": round(accuracy, 6),
        "f1_weighted": round(f1, 6),
        "feature_names": list(X.columns),
        "classes": [int(c) if isinstance(c, (int, float)) else str(c) for c in model.classes_],
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()