#!/usr/bin/env python3
"""Run example calculations from rules/examples/."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.models.calculation import CalculationRequest  # noqa: E402
from app.services.calculation_service import CalculationService  # noqa: E402


def main():
    examples_dir = Path(__file__).resolve().parents[1] / "rules" / "examples"
    service = CalculationService()

    for file_path in sorted(examples_dir.glob("*.json")):
        with open(file_path, encoding="utf-8") as f:
            example = json.load(f)

        request = CalculationRequest(**example["request"])
        result = service.calculate(request)

        print(f"\n--- {file_path.name} ---")
        print(f"  Brand: {result.brand_name}")
        print(f"  Gold value: ¥{result.gold_value}")
        print(f"  Total: ¥{result.total_price}")

        if "expected" in example:
            expected_total = example["expected"].get("total_price")
            if expected_total and abs(result.total_price - expected_total) > 0.01:
                print(f"  ⚠ Expected total ¥{expected_total}, got ¥{result.total_price}")
            else:
                print("  ✓ Matches expected")


if __name__ == "__main__":
    main()
