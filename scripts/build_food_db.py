#!/usr/bin/env python3
"""
Build Food Database Script

RU: CLI: построить итоговый data/food_db.csv.
EN: CLI: build final merged CSV.
"""

import os
import sys

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, "..")
sys.path.insert(0, project_root)

import csv
import json
from datetime import datetime

import dotenv

from core.food_merge import merge_records
from core.food_sources.ciqual import CIQUALAdapter
from core.food_sources.infoods import INFOODSAdapter
from core.food_sources.off import OFFAdapter
from core.food_sources.usda import USDAAdapter
from core.validators import kcal_sanity


def main():
    """Main function to build the food database."""
    print("Building food database...")

    # Load environment variables
    dotenv.load_dotenv()

    # Check feature flags
    enable_infoods = os.getenv("FOOD_ENABLE_INFOODS", "false").lower() == "true"
    enable_ciqual = os.getenv("FOOD_ENABLE_CIQUAL", "false").lower() == "true"

    # Define paths
    usda_path = os.path.join(project_root, "external", "usda_fdc_sample.csv")
    off_path = os.path.join(project_root, "external", "off_products_sample.csv")
    ciqual_path = os.path.join(project_root, "data", "external", "ciqual.csv")
    infoods_path = os.path.join(project_root, "data", "external", "infoods.csv")
    output_path = os.path.join(project_root, "data", "food_db.csv")
    report_path = os.path.join(project_root, "data", "food_merge_report.json")

    streams = []

    # Подключай по мере наличия файлов
    if os.path.isfile(usda_path):
        print(f"Loading USDA data from {usda_path}")
        streams.append(USDAAdapter(usda_path).normalize())
        print("Loaded records from USDA")
    if enable_ciqual and os.path.isfile(ciqual_path):
        print(f"Loading CIQUAL data from {ciqual_path}")
        streams.append(CIQUALAdapter(ciqual_path).normalize())
        print("Loaded records from CIQUAL")
    elif os.path.isfile(ciqual_path):
        print("CIQUAL data available but disabled by feature flag. To enable, set FOOD_ENABLE_CIQUAL=true")
    if enable_infoods and os.path.isfile(infoods_path):
        print(f"Loading INFOODS data from {infoods_path}")
        streams.append(INFOODSAdapter(infoods_path).normalize())
        print("Loaded records from INFOODS")
    elif os.path.isfile(infoods_path):
        print("INFOODS data available but disabled by feature flag. To enable, set FOOD_ENABLE_INFOODS=true")
    if os.path.isfile(off_path):
        print(f"Loading OFF data from {off_path}")
        streams.append(OFFAdapter(off_path, locale="en").normalize())
        print("Loaded records from OFF")

    # Merge records
    print("Merging records...")
    merged = merge_records(streams)
    print(f"Merged into {len(merged)} unique food items")

    # sanity: kcal ≈ 4p+4c+9f
    cleaned = []
    for row in merged:
        if kcal_sanity(kcal=row["kcal"], protein=row["protein_g"], carbs=row["carbs_g"], fat=row["fat_g"]):
            cleaned.append(row)

    # Write to CSV
    print(f"Writing to {output_path}")
    fieldnames = [
        "name", "group", "per_g", "kcal", "protein_g", "fat_g", "carbs_g", "fiber_g",
        "Fe_mg", "Ca_mg", "VitD_IU", "B12_ug", "Folate_ug", "Iodine_ug", "K_mg", "Mg_mg",
        "flags", "price", "source", "version_date"
    ]

    # Write to temporary file first
    temp_path = output_path + ".tmp"
    with open(temp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in cleaned:
            # Convert flags list to string
            row_copy = row.copy()
            if isinstance(row_copy["flags"], list):
                row_copy["flags"] = ";".join(row_copy["flags"])
            writer.writerow(row_copy)

    # Atomically replace the file
    os.replace(temp_path, output_path)
    print(f"Food database written to {output_path}")

    # Generate merge report
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_items": len(cleaned),
        "sources": ["USDA", "CIQUAL" if enable_ciqual else None, "INFOODS" if enable_infoods else None, "OFF"],
        "merge_stats": {},
        "food_groups": {},
        "top_foods_by_nutrient": {}
    }

    # Filter out None values from sources
    report["sources"] = [src for src in report["sources"] if src is not None]

    # Count foods by group
    for item in merged:
        group = item["group"]
        report["food_groups"][group] = report["food_groups"].get(group, 0) + 1

    # Find top foods by key nutrients
    top_nutrients = ["protein_g", "fat_g", "carbs_g", "fiber_g", "Fe_mg", "Ca_mg"]
    for nutrient in top_nutrients:
        sorted_foods = sorted(merged, key=lambda x: x.get(nutrient, 0), reverse=True)[:5]
        report["top_foods_by_nutrient"][nutrient] = [
            {"name": food["name"], "value": food[nutrient]}
            for food in sorted_foods
        ]

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Merge report written to {report_path}")
    print("Food database build complete!")


if __name__ == "__main__":
    main()
