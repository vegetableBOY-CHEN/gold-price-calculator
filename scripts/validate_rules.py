#!/usr/bin/env python3
"""Validate all brand rule JSON files against the schema."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.models.brand import BrandRule  # noqa: E402


def main():
    rules_dir = Path(__file__).resolve().parents[1] / "rules" / "brands"
    if not rules_dir.exists():
        print(f"Rules directory not found: {rules_dir}")
        sys.exit(1)

    errors = []
    for file_path in sorted(rules_dir.glob("*.json")):
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            brand = BrandRule(**data)
            if brand.id != file_path.stem:
                errors.append(f"{file_path.name}: id '{brand.id}' != filename '{file_path.stem}'")
            else:
                print(f"✓ {file_path.name}")
        except Exception as e:
            errors.append(f"{file_path.name}: {e}")

    if errors:
        print("\nValidation failed:")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)

    print(f"\nAll {len(list(rules_dir.glob('*.json')))} brand rules valid.")


if __name__ == "__main__":
    main()
