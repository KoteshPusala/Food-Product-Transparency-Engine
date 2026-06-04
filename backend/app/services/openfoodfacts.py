"""
Step 1: OpenFoodFacts Integration
- Fetch product by barcode or name search
- Parse and normalize the response
"""

import httpx
from typing import Optional, List
from app.models.product import NormalizedProduct, Additive, Nutrient

OFF_BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "ProductTransparencyEngine/1.0 (contact@yourapp.com)"}


# =========================
# Helpers
# =========================

def _parse_additive_tag(tag: str) -> str:
    return tag.replace("en:", "").upper().replace("-", " ")


def _parse_nutrients(nutriments: dict) -> dict[str, Nutrient]:
    THRESHOLDS = {
        "sugars_100g": {"low": 5, "high": 22.5},
        "fat_100g": {"low": 3, "high": 17.5},
        "saturated-fat_100g": {"low": 1.5, "high": 5},
        "salt_100g": {"low": 0.3, "high": 1.5},
        "sodium_100g": {"low": 0.1, "high": 0.6},
        "fiber_100g": {"low": 3, "high": 6},
        "proteins_100g": {"low": 5, "high": 20},
        "energy-kcal_100g": {"low": 100, "high": 400},
    }

    HIGHER_IS_BETTER = {"fiber_100g", "proteins_100g"}

    result: dict[str, Nutrient] = {}

    for key, thresholds in THRESHOLDS.items():
        val = nutriments.get(key)
        if val is None:
            continue

        try:
            val = float(val)
        except (ValueError, TypeError):
            continue

        if key in HIGHER_IS_BETTER:
            level = (
                "high" if val >= thresholds["high"]
                else "low" if val <= thresholds["low"]
                else "moderate"
            )
        else:
            level = (
                "high" if val >= thresholds["high"]
                else "low" if val <= thresholds["low"]
                else "moderate"
            )

        unit_key = key.replace("_100g", "_unit")

        result[key] = Nutrient(
            value=round(val, 2),
            unit=nutriments.get(unit_key, "g"),
            level=level,
        )

    return result


def _normalize(product: dict) -> NormalizedProduct:
    additives_tags = product.get("additives_tags", []) or []

    additives: List[Additive] = []
    for tag in additives_tags:
        readable = _parse_additive_tag(tag)
        additives.append(Additive(code=tag, name=readable))

    ingredients_list = [
        i.get("text", "").strip()
        for i in product.get("ingredients", [])
        if isinstance(i, dict) and i.get("text")
    ]

    allergens_raw = product.get("allergens_hierarchy", []) or []
    allergens = [
        a.replace("en:", "").replace("-", " ").title()
        for a in allergens_raw
    ]

    nova = product.get("nova_group")
    try:
        nova = int(nova) if nova else None
    except (ValueError, TypeError):
        nova = None

    return NormalizedProduct(
        barcode=product.get("code"),
        name=product.get("product_name")
        or product.get("product_name_en")
        or "Unknown Product",
        brand=product.get("brands"),
        image_url=product.get("image_url") or product.get("image_front_url"),
        ingredients_text=product.get("ingredients_text_en")
        or product.get("ingredients_text"),
        ingredients_list=ingredients_list,
        additives=additives,
        nutriscore=(product.get("nutriscore_grade") or "").upper() or None,
        nova_group=nova,
        ecoscore=(product.get("ecoscore_grade") or "").upper() or None,
        nutrients=_parse_nutrients(product.get("nutriments", {})),
        allergens=allergens,
        categories=product.get("categories"),
        countries=product.get("countries"),
    )


# =========================
# API Calls
# =========================

async def fetch_by_barcode(barcode: str) -> Optional[NormalizedProduct]:
    url = f"{OFF_BASE}/api/v2/product/{barcode}.json"

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=httpx.Timeout(20.0, connect=10.0),
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != 1:
            return None

        return _normalize(data["product"])

    except (httpx.RequestError, httpx.ReadTimeout):
        return None
    except Exception:
        return None


async def search_by_name(
    query: str,
    page: int = 1,
    page_size: int = 5,
) -> list[NormalizedProduct]:

    url = f"{OFF_BASE}/cgi/search.pl"

    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": (
            "code,product_name,product_name_en,brands,image_url,image_front_url,"
            "ingredients_text,ingredients_text_en,ingredients,additives_tags,"
            "nutriscore_grade,nova_group,ecoscore_grade,nutriments,"
            "allergens_hierarchy,categories,countries"
        ),
    }

    try:
        async with httpx.AsyncClient(
            headers=HEADERS,
            timeout=httpx.Timeout(30.0, connect=10.0),
        ) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

    except (httpx.RequestError, httpx.ReadTimeout):
        return []
    except Exception:
        return []

    products = data.get("products", []) or []

    results: list[NormalizedProduct] = []

    for p in products:
        try:
            results.append(_normalize(p))
        except Exception:
            continue

    return results