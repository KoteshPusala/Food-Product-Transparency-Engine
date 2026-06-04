"""
Product Transparency Engine — FastAPI Backend
Run with: uvicorn app.main:app --reload
"""

from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.products import router
from app.routes.audit import router as audit_router


app = FastAPI(
    title="Product Transparency Engine API",
    description="Analyze food products for health risks using OpenFoodFacts, PubChem, PubMed, and Gemini AI",
    version="1.0.0",
)

# Allow Next.js frontend (localhost:3000) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(audit_router) 


@app.get("/")
async def root():
    return {
        "message": "Product Transparency Engine API",
        "docs": "/docs",
        "endpoints": {
            "analyze_by_barcode": "/api/product/barcode/{barcode}",
            "search_products": "/api/product/search?q={name}",
            "search_and_analyze": "/api/product/search/analyze?q={name}",
            "pubchem_lookup": "/api/ingredient/pubchem?name={ingredient}",
            "pubmed_papers": "/api/ingredient/papers?ingredient={name}",
        }
    }