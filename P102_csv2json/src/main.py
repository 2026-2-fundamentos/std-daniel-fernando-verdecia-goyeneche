import csv
import json
from pathlib import Path

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = next(ACTIVITY_DIR.rglob("drivers.csv"))
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "drivers.json"
FIELDS = ["driverId", "name", "certified", "wage-plan"]


def main():
    with open(INPUT_FILE, encoding="utf-8-sig", newline="") as f:
        records = [{field: row[field] for field in FIELDS} for row in csv.DictReader(f)]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()