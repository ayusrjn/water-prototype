"""Simple OpenCV inference demo for WATER execution tests."""

from __future__ import annotations

import json
from pathlib import Path

import cv2


def main() -> None:
    input_dir = Path("/data/input")
    images = sorted(
        [p for p in input_dir.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    )

    results = []
    for image_path in images:
        image = cv2.imread(str(image_path))
        if image is None:
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_intensity = float(gray.mean())
        prediction = "bright" if mean_intensity >= 127 else "dark"
        results.append(
            {
                "file": image_path.name,
                "mean_intensity": round(mean_intensity, 2),
                "prediction": prediction,
            }
        )

    print(json.dumps({"images_processed": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
