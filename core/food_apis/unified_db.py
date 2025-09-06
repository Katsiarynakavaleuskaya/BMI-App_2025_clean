"""
Unified Food Database Interface

RU: Единый интерфейс для работы с различными API продуктов питания.
EN: Unified interface for working with different food nutrition APIs.

This module provides a single interface to access multiple food databases
(USDA, Open Food Facts, etc.) and cache results for better performance.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .ciqual_client import CIQUALFoodItem
    from .fao_infoods_client import FAOInfoodsFoodItem
    from .openfoodfacts_client import OFFFoodItem

from .usda_client import USDAClient, USDAFoodItem

# Try to import Open Food Facts client
try:
    from .openfoodfacts_client import OFFClient
    OFF_AVAILABLE = True
except ImportError:
    OFFClient = None
    OFF_AVAILABLE = False

# Try to import FAO/INFOODS client
try:
    from .fao_infoods_client import FAOInfoodsClient
    FAO_INFOODS_AVAILABLE = True
except ImportError:
    FAOInfoodsClient = None
    FAO_INFOODS_AVAILABLE = False

# Try to import CIQUAL client
try:
    from .ciqual_client import CIQUALClient
    CIQUAL_AVAILABLE = True
except ImportError:
    CIQUALClient = None
    CIQUAL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class UnifiedFoodItem:
    """
    RU: Унифицированный элемент продукта из различных источников.
    EN: Unified food item from different sources.
    """
    name: str
    nutrients_per_100g: Dict[str, float]
    cost_per_100g: float
    tags: List[str]
    availability_regions: List[str]
    source: str
    source_id: str
    category: Optional[str] = None

    @classmethod
    def from_usda_item(
        cls,
        usda_item: USDAFoodItem,
        estimated_cost: float = 1.0
    ) -> 'UnifiedFoodItem':
        """Convert USDA item to unified format."""
        return cls(
            name=usda_item.description,
            nutrients_per_100g=usda_item.nutrients_per_100g,
            cost_per_100g=estimated_cost,
            tags=usda_item._generate_tags(),
            availability_regions=["US", "BY", "RU"],  # Assume global availability
            source="USDA FoodData Central",
            source_id=str(usda_item.fdc_id),
            category=usda_item.food_category
        )

    @classmethod
    def from_off_item(
        cls,
        off_item: OFFFoodItem,
        estimated_cost: float = 1.5
    ) -> 'UnifiedFoodItem':
        """Convert Open Food Facts item to unified format."""
        return cls(
            name=off_item.product_name,
            nutrients_per_100g=off_item.nutrients_per_100g,
            cost_per_100g=estimated_cost,
            tags=off_item._generate_tags(),
            availability_regions=off_item.countries,
            source="Open Food Facts",
            source_id=off_item.code,
            category=off_item.categories[0] if off_item.categories else None
        )

    @classmethod
    def from_fao_infoods_item(
        cls,
        fao_item: FAOInfoodsFoodItem,
        estimated_cost: float = 1.2
    ) -> 'UnifiedFoodItem':
        """Convert FAO/INFOODS item to unified format."""
        return cls(
            name=fao_item.food_name,
            nutrients_per_100g=fao_item.nutrients_per_100g,
            cost_per_100g=estimated_cost,
            tags=fao_item._generate_tags(),
            availability_regions=[fao_item.region],
            source=f"FAO/INFOODS {fao_item.database_source}",
            source_id=fao_item.food_id,
            category=fao_item.food_group
        )

    @classmethod
    def from_ciqual_item(
        cls,
        ciqual_item: CIQUALFoodItem,
        estimated_cost: float = 1.3
    ) -> 'UnifiedFoodItem':
        """Convert CIQUAL item to unified format."""
        return cls(
            name=ciqual_item.food_name_fr or ciqual_item.food_name_en,
            nutrients_per_100g=ciqual_item.nutrients_per_100g,
            cost_per_100g=estimated_cost,
            tags=ciqual_item._generate_tags(),
            availability_regions=[ciqual_item.region],
            source=f"CIQUAL {ciqual_item.database_source}",
            source_id=ciqual_item.food_code,
            category=ciqual_item.food_group
        )

    def to_menu_engine_format(self) -> Dict[str, Any]:
        """Convert to format expected by menu_engine.py"""
        return {
            "name": self.name,
            "nutrients_per_100g": self.nutrients_per_100g,
            "cost_per_100g": self.cost_per_100g,
            "tags": self.tags,
            "availability_regions": self.availability_regions,
            "source": self.source,
            "source_id": self.source_id,
            "category": self.category
        }


class UnifiedFoodDatabase:
    """
    RU: Единая база данных продуктов с кэшированием и поддержкой нескольких источников.
    EN: Unified food database with caching and multiple source support.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.usda_client = USDAClient()
        self.off_client = OFFClient() if OFF_AVAILABLE and OFFClient is not None else None
        self.fao_infoods_client = FAOInfoodsClient() if FAO_INFOODS_AVAILABLE and FAOInfoodsClient is not None else None
        self.ciqual_client = CIQUALClient() if CIQUAL_AVAILABLE and CIQUALClient is not None else None
        self.cache_dir = Path(cache_dir or "cache/food_db")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for this session
        self._memory_cache: Dict[str, UnifiedFoodItem] = {}

        # Load persistent cache
        self._load_cache()

    def _get_cache_file(self) -> Path:
        """Get path to cache file."""
        return self.cache_dir / "unified_food_cache.json"

    def _load_cache(self):
        """Load cached food items from disk."""
        cache_file = self._get_cache_file()
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                for key, item_data in cache_data.items():
                    self._memory_cache[key] = UnifiedFoodItem(**item_data)

                logger.info(f"Loaded {len(self._memory_cache)} items from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")

    def _save_cache(self):
        """Save cached food items to disk."""
        try:
            cache_data = {
                key: asdict(item) for key, item in self._memory_cache.items()
            }

            with open(self._get_cache_file(), 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(cache_data)} items to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    async def search_food(self, query: str, prefer_source: str = "usda") -> List[UnifiedFoodItem]:  # pragma: no cover (network-bound, covered by integration elsewhere)
        """
        RU: Поиск продуктов по названию.
        EN: Search for foods by name.

        Args:
            query: Search query (e.g., "chicken breast")
            prefer_source: Preferred data source ("usda", "openfoodfacts", "fao_infoods", "ciqual")

        Returns:
            List of unified food items
        """
        # Check cache first
        cache_key = f"search_{query.lower().strip()}"
        if cache_key in self._memory_cache:
            return [self._memory_cache[cache_key]]

        results = []

        # Search based on preferred source
        if prefer_source == "usda":
            # Search USDA first
            usda_results = await self.usda_client.search_foods(query, page_size=5)
            for usda_item in usda_results:
                unified_item = UnifiedFoodItem.from_usda_item(usda_item)
                results.append(unified_item)

                # Cache the best result
                if not self._memory_cache.get(cache_key):
                    self._memory_cache[cache_key] = unified_item

        elif prefer_source == "openfoodfacts" and self.off_client:
            # Search Open Food Facts
            try:
                off_results = await self.off_client.search_products(query, page_size=5)
                for off_item in off_results:
                    unified_item = UnifiedFoodItem.from_off_item(off_item)
                    results.append(unified_item)

                    # Cache the best result
                    if not self._memory_cache.get(cache_key):
                        self._memory_cache[cache_key] = unified_item
            except Exception as e:
                logger.error(f"Error searching Open Food Facts: {e}")

        elif prefer_source == "fao_infoods" and self.fao_infoods_client:
            # Search FAO/INFOODS
            try:
                fao_results = self.fao_infoods_client.search_foods(query)
                for fao_item in fao_results[:5]:  # Limit to 5 results
                    unified_item = UnifiedFoodItem.from_fao_infoods_item(fao_item)
                    results.append(unified_item)

                    # Cache the best result
                    if not self._memory_cache.get(cache_key):
                        self._memory_cache[cache_key] = unified_item
            except Exception as e:
                logger.error(f"Error searching FAO/INFOODS: {e}")

        elif prefer_source == "ciqual" and self.ciqual_client:
            # Search CIQUAL
            try:
                ciqual_results = self.ciqual_client.search_foods(query)
                for ciqual_item in ciqual_results[:5]:  # Limit to 5 results
                    unified_item = UnifiedFoodItem.from_ciqual_item(ciqual_item)
                    results.append(unified_item)

                    # Cache the best result
                    if not self._memory_cache.get(cache_key):
                        self._memory_cache[cache_key] = unified_item
            except Exception as e:
                logger.error(f"Error searching CIQUAL: {e}")

        # If no results from preferred source, search other sources
        if not results:
            # Search USDA
            usda_results = await self.usda_client.search_foods(query, page_size=5)
            for usda_item in usda_results:
                unified_item = UnifiedFoodItem.from_usda_item(usda_item)
                results.append(unified_item)

                # Cache the best result
                if not self._memory_cache.get(cache_key):
                    self._memory_cache[cache_key] = unified_item

            # Search Open Food Facts if USDA results are empty
            if not results and self.off_client:
                try:
                    off_results = await self.off_client.search_products(query, page_size=5)
                    for off_item in off_results:
                        unified_item = UnifiedFoodItem.from_off_item(off_item)
                        results.append(unified_item)

                        # Cache the best result
                        if not self._memory_cache.get(cache_key):
                            self._memory_cache[cache_key] = unified_item
                except Exception as e:
                    logger.error(f"Error searching Open Food Facts: {e}")

            # Search FAO/INFOODS if other results are empty
            if not results and self.fao_infoods_client:
                try:
                    fao_results = self.fao_infoods_client.search_foods(query)
                    for fao_item in fao_results[:5]:  # Limit to 5 results
                        unified_item = UnifiedFoodItem.from_fao_infoods_item(fao_item)
                        results.append(unified_item)

                        # Cache the best result
                        if not self._memory_cache.get(cache_key):
                            self._memory_cache[cache_key] = unified_item
                except Exception as e:
                    logger.error(f"Error searching FAO/INFOODS: {e}")

            # Search CIQUAL if other results are empty
            if not results and self.ciqual_client:
                try:
                    ciqual_results = self.ciqual_client.search_foods(query)
                    for ciqual_item in ciqual_results[:5]:  # Limit to 5 results
                        unified_item = UnifiedFoodItem.from_ciqual_item(ciqual_item)
                        results.append(unified_item)

                        # Cache the best result
                        if not self._memory_cache.get(cache_key):
                            self._memory_cache[cache_key] = unified_item
                except Exception as e:
                    logger.error(f"Error searching CIQUAL: {e}")

        if results:
            self._save_cache()

        return results

    async def get_food_by_id(self, source: str, food_id: str) -> Optional[UnifiedFoodItem]:  # pragma: no cover (network-bound)
        """
        RU: Получить продукт по ID источника.
        EN: Get food by source ID.
        """
        cache_key = f"{source}_{food_id}"
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        if source == "usda":
            try:
                fdc_id = int(food_id)
                usda_item = await self.usda_client.get_food_details(fdc_id)
                if usda_item:
                    unified_item = UnifiedFoodItem.from_usda_item(usda_item)
                    self._memory_cache[cache_key] = unified_item
                    self._save_cache()
                    return unified_item
            except ValueError:
                logger.error(f"Invalid USDA FDC ID: {food_id}")

        elif source == "openfoodfacts" and self.off_client:
            try:
                off_item = await self.off_client.get_product_details(food_id)
                if off_item:
                    unified_item = UnifiedFoodItem.from_off_item(off_item)
                    self._memory_cache[cache_key] = unified_item
                    self._save_cache()
                    return unified_item
            except Exception as e:
                logger.error(f"Error fetching Open Food Facts item {food_id}: {e}")

        elif source == "fao_infoods" and self.fao_infoods_client:
            try:
                # Extract database name and food ID from food_id (format: database:food_id)
                parts = food_id.split(":", 1)
                if len(parts) == 2:
                    database_name, actual_food_id = parts
                    fao_item = self.fao_infoods_client.get_food_by_id(actual_food_id, database_name)
                    if fao_item:
                        unified_item = UnifiedFoodItem.from_fao_infoods_item(fao_item)
                        self._memory_cache[cache_key] = unified_item
                        self._save_cache()
                        return unified_item
            except Exception as e:
                logger.error(f"Error fetching FAO/INFOODS item {food_id}: {e}")

        elif source == "ciqual" and self.ciqual_client:
            try:
                ciqual_item = self.ciqual_client.get_food_by_code(food_id)
                if ciqual_item:
                    unified_item = UnifiedFoodItem.from_ciqual_item(ciqual_item)
                    self._memory_cache[cache_key] = unified_item
                    self._save_cache()
                    return unified_item
            except Exception as e:
                logger.error(f"Error fetching CIQUAL item {food_id}: {e}")

        return None

    async def get_common_foods_database(self) -> Dict[str, UnifiedFoodItem]:  # pragma: no cover (network-bound helper)
        """
        RU: Получает базу часто используемых продуктов.
        EN: Gets database of commonly used foods.

        Returns a dictionary of common foods with standardized names.
        """
        # Check if we have cached common foods
        cache_file = self.cache_dir / "common_foods.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                foods_db = {}
                for key, item_data in cache_data.items():
                    foods_db[key] = UnifiedFoodItem(**item_data)

                logger.info(f"Loaded {len(foods_db)} common foods from cache")
                # If cache contains data, return it; otherwise fall through to rebuild
                if foods_db:
                    return foods_db
            except Exception as e:
                logger.error(f"Error loading common foods cache: {e}")

        # Try delegated helper from USDA client if available (enables easy mocking in tests)
        try:
            from .usda_client import get_common_foods_database as _get_common_usda  # type: ignore
        except Exception:  # pragma: no cover - optional import
            _get_common_usda = None  # type: ignore

        if _get_common_usda is not None:
            try:
                usda_map = await _get_common_usda()
                if usda_map:
                    foods_db = {k: UnifiedFoodItem.from_usda_item(v) for k, v in usda_map.items()}
                    # Save cache for future runs
                    try:
                        cache_data = {key: asdict(item) for key, item in foods_db.items()}
                        with open(cache_file, 'w', encoding='utf-8') as f:
                            json.dump(cache_data, f, indent=2, ensure_ascii=False)
                        logger.info(f"Saved {len(foods_db)} common foods to cache via delegated USDA helper")
                    except Exception as e:
                        logger.error(f"Error saving common foods cache: {e}")
                    return foods_db
            except Exception as e:  # pragma: no cover - network/path dependent
                logger.error(f"Delegated USDA common foods fetch failed: {e}")

        # Build common foods database from multiple sources
        common_searches = {
            "chicken_breast": "chicken breast meat only cooked roasted",
            "salmon": "salmon atlantic farmed cooked dry heat",
            "lentils": "lentils mature seeds cooked boiled",
            "spinach": "spinach raw",
            "oats": "cereals oats regular and quick unenriched dry",
            "broccoli": "broccoli raw",
            "brown_rice": "rice brown long-grain cooked",
            "quinoa": "quinoa cooked",
            "almonds": "nuts almonds",
            "greek_yogurt": "yogurt greek plain nonfat",
            "eggs": "egg whole raw fresh",
            "sweet_potato": "sweet potato raw unprepared",
            "avocado": "avocados raw all commercial varieties",
            "banana": "bananas raw",
            "black_beans": "beans black mature seeds cooked boiled",
            "tofu": "tofu raw firm prepared with calcium sulfate",
            "olive_oil": "oil olive salad or cooking",
            "milk": "milk reduced fat fluid 2% milkfat",
            "carrots": "carrots raw",
            "tomatoes": "tomatoes red ripe raw year round average"
        }

        foods_db = {}

        for standard_name, search_query in common_searches.items():
            try:
                # Try to get from any available source
                results = await self.search_food(search_query)
                if results:
                    # Take the first result (usually most relevant)
                    foods_db[standard_name] = results[0]
                    logger.info(f"Found food for {standard_name}: {results[0].name}")

                # Small delay to be respectful to the API
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching {standard_name}: {e}")
                continue

        # Save common foods cache
        try:
            cache_data = {key: asdict(item) for key, item in foods_db.items()}
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(foods_db)} common foods to cache")
        except Exception as e:
            logger.error(f"Error saving common foods cache: {e}")

        return foods_db

    async def close(self):
        """Close all API clients."""
        await self.usda_client.close()
        if self.off_client:
            await self.off_client.close()
        # File-based clients don't need to be closed


# Global instance for easy access
_unified_db_instance: Optional[UnifiedFoodDatabase] = None


async def get_unified_food_db() -> UnifiedFoodDatabase:
    """
    RU: Получить глобальный экземпляр унифицированной базы данных продуктов.
    EN: Get global instance of unified food database.
    """
    global _unified_db_instance
    if _unified_db_instance is None:
        _unified_db_instance = UnifiedFoodDatabase()
    return _unified_db_instance


async def search_foods_unified(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    RU: Упрощенная функция поиска продуктов для использования в menu_engine.
    EN: Simplified food search function for use in menu_engine.

    Returns results in the format expected by menu_engine.py
    """
    db = await get_unified_food_db()
    results = await db.search_food(query)

    return [item.to_menu_engine_format() for item in results[:max_results]]


if __name__ == "__main__":
    # Test the unified database
    async def test_unified_db():
        db = UnifiedFoodDatabase()

        try:
            print("Testing unified food database...")

            # Test search
            results = await db.search_food("chicken breast")
            if results:
                food = results[0]
                print(f"✓ Found: {food.name}")
                print(f"✓ Source: {food.source}")
                print(f"✓ Nutrients: {len(food.nutrients_per_100g)} found")
                print(f"✓ Tags: {food.tags}")

            # Test common foods database
            print("\nBuilding common foods database...")
            common_foods = await db.get_common_foods_database()
            print(f"✓ Built database with {len(common_foods)} common foods:")
            for name, food in list(common_foods.items())[:5]:
                print(f"  {name}: {food.name}")

        finally:
            await db.close()

    # Run test
    asyncio.run(test_unified_db())
