from fastapi import APIRouter
from pydantic import BaseModel
from app.services import openfoodfacts
from app.services.products import run_full_analysis

router = APIRouter(prefix="/api", tags=["audit"])


class AuditRequest(BaseModel):
    barcode: str
    include_ai: bool = True


@router.post("/audit")
async def audit(data: AuditRequest):
    product = await openfoodfacts.fetch_by_barcode(data.barcode)

    if not product:
        return {"error": "Product not found"}

    return await run_full_analysis(product, data.include_ai)