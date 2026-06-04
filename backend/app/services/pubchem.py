"""
Step 3: PubChem Ingredient Enrichment
- Look up ingredients by name to get safety data
- Cache results to avoid repeated API calls
"""

import asyncio
import httpx
from cachetools import TTLCache
from app.models.product import PubChemData

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Cache: max 500 entries, TTL 24 hours
_cache: TTLCache = TTLCache(maxsize=500, ttl=86400)

# GHS hazard statement prefixes that indicate health concern
HEALTH_HAZARD_PREFIXES = ("H3", "H4")


async def _get_cid(name: str) -> int | None:
    """Get PubChem CID for a compound name."""
    try:
        encoded = httpx.URL("", params={"name": name})
        url = f"{PUBCHEM_BASE}/compound/name/{name}/cids/JSON"
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return cids[0] if cids else None
    except Exception:
        return None


async def _get_properties(cid: int) -> dict:
    """Get basic compound properties."""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/IUPACName,MolecularFormula/JSON"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
            return props
    except Exception:
        return {}


async def _get_ghs_hazards(cid: int) -> list[str]:
    """Get GHS hazard statements from PubChem Safety & Hazards section."""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/JSON"
    hazards = []
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        sections = data.get("Record", {}).get("Section", [])
        for section in sections:
            if section.get("TOCHeading") == "Safety and Hazards":
                for sub in section.get("Section", []):
                    if "GHS" in sub.get("TOCHeading", ""):
                        for subsub in sub.get("Section", []):
                            if "Hazard" in subsub.get("TOCHeading", ""):
                                for info in subsub.get("Information", []):
                                    for val in info.get("Value", {}).get("StringWithMarkup", []):
                                        text = val.get("String", "")
                                        if text.startswith("H") and len(text) > 3:
                                            hazards.append(text)
    except Exception:
        pass
    return list(set(hazards))


def _is_harmful(hazards: list[str]) -> bool:
    return any(h.startswith(HEALTH_HAZARD_PREFIXES) for h in hazards)


async def enrich_ingredient(ingredient: str) -> PubChemData:
    """Full enrichment pipeline for a single ingredient name."""
    cache_key = ingredient.lower().strip()
    if cache_key in _cache:
        return _cache[cache_key]

    result = PubChemData(ingredient=ingredient)

    cid = await _get_cid(ingredient)
    if cid:
        result.cid = cid
        props = await _get_properties(cid)
        result.iupac_name = props.get("IUPACName")
        result.molecular_formula = props.get("MolecularFormula")
        hazards = await _get_ghs_hazards(cid)
        result.hazard_statements = hazards
        result.is_harmful = _is_harmful(hazards)
        if hazards:
            result.safety_summary = f"Found {len(hazards)} GHS hazard statement(s): " + "; ".join(hazards[:3])
        else:
            result.safety_summary = "No significant GHS hazard statements found."
    else:
        result.safety_summary = "Compound not found in PubChem database."

    _cache[cache_key] = result
    return result


async def enrich_ingredients_batch(ingredients: list[str], max_items: int = 10) -> list[PubChemData]:
    """Enrich multiple ingredients (limit to avoid too many API calls)."""
    targets = ingredients[:max_items]
    tasks = [enrich_ingredient(ing) for ing in targets]
    return await asyncio.gather(*tasks)