#!/usr/bin/env python3
"""
Script to run the Food Database Merge Pipeline

RU: Скрипт для запуска пайплайна мерджа базы данных продуктов.
EN: Script to run the food database merge pipeline.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # Import after path setup
    from core.food_merge_pipeline import run_food_merge_pipeline

    parser = argparse.ArgumentParser(description="Run Food Database Merge Pipeline")
    parser.add_argument(
        "--queries",
        nargs="+",
        default=[
            "chicken breast", "salmon", "spinach", "tofu", "lentils",
            "oats", "brown rice", "olive oil", "banana", "greek yogurt",
            "beef", "pork", "eggs", "milk", "cheese",
            "broccoli", "carrots", "apples", "oranges", "berries"
        ],
        help="Food queries to search for (default: common foods)"
    )
    parser.add_argument(
        "--output",
        default="food_db_merged.csv",
        help="Output CSV filename (default: food_db_merged.csv)"
    )

    args = parser.parse_args()

    logger.info("Starting food database merge pipeline")
    logger.info(f"Queries: {args.queries}")
    logger.info(f"Output file: {args.output}")

    try:
        # Run the pipeline with provided arguments
        asyncio.run(run_food_merge_pipeline(args.queries, args.output))
        logger.info("Food database merge pipeline completed successfully")
    except Exception as e:
        logger.error(f"Error running food database merge pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
