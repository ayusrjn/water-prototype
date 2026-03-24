"""Train a Random Forest model, extract feature importance, and save the model."""

from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def main() -> None:
    # 1. Setup paths
    csv_path_str = os.environ.get("DATA_CSV", "/data/input/dataset.csv")
    csv_path = Path(csv_path_str)
    
    output_dir = Path("/data/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load Data
    if csv_path.is_file():
        df = pd.read_csv(csv_path)
        if df.shape[1] < 2:
            raise SystemExit("CSV needs at least one feature column and one target column.")
            
        target_col = os.environ.get("TARGET_COL", df.columns[-1])
        X = df.drop(columns=[target_col])
        y = df[target_col]
        dataset_source = str(csv_path)
        feature_names = list(X.columns)
    else:
        # Fallback to Iris
        iris = load_iris(as_frame=True)
        X = iris.data
        y = iris.target
        target_col = "target (iris species)"
        dataset_source = "sklearn.datasets.load_iris"
        feature_names = iris.feature_names

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 3. Train the Model (Medium complexity: 100 trees, no grid search needed)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 4. Evaluate
    pred = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, pred))
    f1 = float(f1_score(y_test, pred, average="weighted"))

    # Extract feature importances
    importances = {
        name: round(float(imp), 4) 
        for name, imp in zip(feature_names, model.feature_importances_)
    }

    # 5. Serialize and Save the Model
    model_path = output_dir / "rf_model.pkl"
    joblib.dump(model, model_path)

    out = {
        "dataset_source": dataset_source,
        "n_samples": int(len(X)),
        "accuracy": round(accuracy, 6),
        "f1_weighted": round(f1, 6),
        "feature_importances": importances,
        "model_saved_to": str(model_path)
    }
    
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()