"""
API Routes for Product Transparency Engine
"""

import asyncio
from fastapi import APIRouter, HTTPException, Query
from app.models.product import ProductAnalysisResponse, NormalizedProduct
from app.services import openfoodfacts
from app.services import health_score
from app.services import pubchem
from app.services import pubmed
from app.services import ai_agent

router = APIRouter(prefix="/api", tags=["products"])


async def run_full_analysis(product: NormalizedProduct, include_ai: bool) -> ProductAnalysisResponse:
    """Shared analysis pipeline used by both barcode and search endpoints."""

    # Step 2: Health score
    score = health_score.calculate_health_score(product)

    # Identify ingredients needing enrichment
    flagged_additives = [a.name for a in product.additives if a.code.lower() in health_score.HARMFUL_ADDITIVES]
    harmful_ingredients = health_score.get_harmful_ingredients(product)

    enrichment_targets = list(set(
        flagged_additives + product.ingredients_list[:5]
    ))[:10]

    try:
        pubchem_results = await pubchem.enrich_ingredients_batch(enrichment_targets)
    except Exception as e:
        print("PUBCHEM ERROR:", e)
        pubchem_results = []

    try:
        papers = await pubmed.search_papers_for_multiple(harmful_ingredients[:4])
    except Exception as e:
        print("PUBMED ERROR:", e)
        papers = []

    ai_analysis = None
    if include_ai:
        try:
            ai_analysis = await ai_agent.analyze_product(product, score, pubchem_results, papers)
        except Exception as e:
            print("AI ERROR:", e)
            ai_analysis = None
    return ProductAnalysisResponse(
        product=product,
        score=score,
        ai_analysis=ai_analysis,
        top_papers=papers[:6],
    )


@router.get("/product/barcode/{barcode}", response_model=ProductAnalysisResponse)
async def analyze_by_barcode(
    barcode: str,
    include_ai: bool = Query(default=True, description="Include Groq AI analysis")
):
    """Fetch and analyze a product by its barcode."""
    product = await openfoodfacts.fetch_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with barcode '{barcode}' not found.")
    return await run_full_analysis(product, include_ai)


@router.get("/product/search", response_model=list[NormalizedProduct])
async def search_products(
    q: str = Query(..., min_length=2, description="Product name to search"),
    page_size: int = Query(default=5, ge=1, le=20),
):
    """Search products by name."""
    results = await openfoodfacts.search_by_name(q, page_size=page_size)
    if not results:
        raise HTTPException(status_code=404, detail=f"No products found for '{q}'.")
    return results


@router.get("/product/search/analyze", response_model=ProductAnalysisResponse)
async def search_and_analyze(
    q: str = Query(..., min_length=2, description="Product name to search and analyze"),
    include_ai: bool = Query(default=True, description="Include AI analysis")
):
    """Search by name and run full analysis on the first result."""
    results = await openfoodfacts.search_by_name(q, page_size=1)
    if not results:
        raise HTTPException(status_code=404, detail=f"No products found for '{q}'.")
    return await run_full_analysis(results[0], include_ai)


@router.get("/ingredient/pubchem")
async def get_pubchem_data(name: str = Query(..., min_length=2)):
    """Lookup a single ingredient in PubChem."""
    result = await pubchem.enrich_ingredient(name)
    return result


@router.get("/ingredient/papers")
async def get_research_papers(
    ingredient: str = Query(..., min_length=2),
    max_results: int = Query(default=3, ge=1, le=10)
):
    """Fetch PubMed research papers for a specific ingredient."""
    papers = await pubmed.search_papers(ingredient, max_results)
    return papers


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Product Transparency Engine Backend"}