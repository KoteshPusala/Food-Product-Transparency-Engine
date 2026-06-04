"""
Step 4: PubMed Research Paper Fetching
"""

import os
import asyncio
import httpx
from cachetools import TTLCache
from app.models.product import ResearchPaper

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

_cache: TTLCache = TTLCache(maxsize=200, ttl=43200)


def _base_params() -> dict:
    params = {"retmode": "json"}
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    return params


async def _search_pmids(query: str, max_results: int = 5) -> list[str]:
    params = _base_params()
    params.update({
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "relevance",
        "usehistory": "n",
    })
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{ENTREZ_BASE}/esearch.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


async def _fetch_summaries(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []

    params = _base_params()
    params.update({
        "db": "pubmed",
        "id": ",".join(pmids),
    })

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(f"{ENTREZ_BASE}/esummary.fcgi", params=params)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        
        # Remove the 'uids' key safely
        return [
            v for k, v in result.items()
            if k != "uids" and isinstance(v, dict)
        ]

    except Exception:
        return []

def _parse_paper(summary: dict, abstract: str, query: str) -> ResearchPaper | None:
    try:
        pmid = str(summary.get("uid", ""))
        if not pmid or pmid == "uids":
            return None
        title = summary.get("title", "No title available")
        authors = [a.get("name", "") for a in summary.get("authors", [])[:3]]
        journal = summary.get("fulljournalname", summary.get("source", ""))
        pub_date = summary.get("pubdate", "")
        year = pub_date[:4] if pub_date else None

        articleids = summary.get("articleids", [])
        pmc_id = next((a["value"] for a in articleids if a.get("idtype") == "pmc"), None)
        is_open = bool(pmc_id)
        url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/" if pmc_id else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return ResearchPaper(
            pmid=pmid,
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            abstract=abstract,
            url=url,
            is_open_access=is_open,
            ingredient_query=query,
        )
    except Exception:
        return None


async def search_papers(ingredient: str, max_results: int = 3) -> list[ResearchPaper]:
    cache_key = f"{ingredient.lower().strip()}:{max_results}"
    if cache_key in _cache:
        return _cache[cache_key]

    query = f'"{ingredient}"[Title/Abstract] AND (health effects OR toxicity OR safety OR adverse effects)'
    pmids = await _search_pmids(query, max_results)
    if not pmids:
        return []

    summaries = await _fetch_summaries(pmids)

    papers = []
    for summary in summaries:
        pmid = str(summary.get("uid", ""))
        paper = _parse_paper(summary, "", query)
        if paper:
            papers.append(paper)

    papers.sort(key=lambda p: (not p.is_open_access, p.year or "0000"))
    _cache[cache_key] = papers
    return papers


async def search_papers_for_multiple(ingredients: list[str], papers_per_ingredient: int = 2) -> list[ResearchPaper]:
    """Fetch papers for multiple harmful ingredients."""
    if not ingredients:
        return []
    all_papers = []
    tasks = [search_papers(ing, papers_per_ingredient) for ing in ingredients[:5]]
    results = await asyncio.gather(*tasks)
    for paper_list in results:
        all_papers.extend(paper_list)
    return all_papers