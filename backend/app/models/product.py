from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class Nutrient(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    level: Optional[str] = None  # low / moderate / high


class Additive(BaseModel):
    code: str
    name: str
    risk_level: Optional[str] = None
    pubchem_cid: Optional[int] = None
    description: Optional[str] = None


class NormalizedProduct(BaseModel):
    barcode: Optional[str] = None
    name: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    ingredients_text: Optional[str] = None
    ingredients_list: List[str] = Field(default_factory=list)
    additives: List[Additive] = Field(default_factory=list)
    nutriscore: Optional[str] = None
    nova_group: Optional[int] = None
    ecoscore: Optional[str] = None
    nutrients: Dict[str, Nutrient] = Field(default_factory=dict)
    allergens: List[str] = Field(default_factory=list)
    categories: Optional[str] = None
    countries: Optional[str] = None


class ScoreBreakdown(BaseModel):
    nutriscore_score: float
    nova_score: float
    additives_score: float
    nutrient_score: float
    total: float
    grade: str
    summary: str


class PubChemData(BaseModel):
    ingredient: str
    cid: Optional[int] = None
    iupac_name: Optional[str] = None
    molecular_formula: Optional[str] = None
    hazard_statements: List[str] = Field(default_factory=list)
    safety_summary: Optional[str] = None
    is_harmful: bool = False


class ResearchPaper(BaseModel):
    pmid: str
    title: str
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    year: Optional[str] = None
    abstract: Optional[str] = None
    url: str
    is_open_access: bool = False
    ingredient_query: str


class IngredientAnalysis(BaseModel):
    name: str
    status: str
    explanation: str
    pubchem_data: Optional[PubChemData] = None
    papers: List[ResearchPaper] = Field(default_factory=list)


class AIAnalysis(BaseModel):
    overall_verdict: str
    overall_summary: str
    ingredient_analyses: List[IngredientAnalysis] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    safer_alternatives: Optional[str] = None


class ProductAnalysisResponse(BaseModel):
    product: NormalizedProduct
    score: ScoreBreakdown
    ai_analysis: Optional[AIAnalysis] = None
    top_papers: List[ResearchPaper] = Field(default_factory=list)
    error: Optional[str] = None