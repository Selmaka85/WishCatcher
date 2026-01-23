"""
Pydantic Models pentru API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# Enums
class Domain(str, Enum):
    SOFTWARE = "software"
    EDUCATION = "education"
    HEALTH = "health"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    LOGISTICS = "logistics"
    OTHER = "other"


class Feasibility(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IMPOSSIBLE = "impossible"


class MarketSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# Health Response
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


# WishCatcher Models
class TriggerAnalysis(BaseModel):
    trigger: Optional[Dict[str, Any]] = Field(default=None)
    frustration: Optional[Dict[str, Any]] = Field(default=None)
    pain_points: List[Dict[str, Any]] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = Field(default=None)
    emotional_intensity: float = Field(default=0.0, ge=0.0, le=1.0)


class WishData(BaseModel):
    id: str
    intent: str  # intent_short (pentru afișare)
    domain: str
    score: float
    business_score: float
    technologies: List[str] = Field(default_factory=list)
    feasibility: str
    trigger_analysis: Optional[TriggerAnalysis] = None
    source: str
    timestamp: datetime
    frequency: int = 1
    market_analysis: Optional[Dict[str, Any]] = None
    monetization: Optional[Dict[str, Any]] = None
    # Câmpuri noi pentru structură completă
    intent_full: Optional[str] = None  # Intent complet (3-5 propoziții)
    structured: Optional[Dict[str, Any]] = None  # Structură detaliată (what, why, who, when, how, etc.)
    # Câmpuri noi pentru prioritizare și validare
    priority_score: Optional[float] = None  # Priority score (0-1)
    urgency: Optional[str] = None  # "low", "medium", "high", "critical"
    timing: Optional[str] = None  # "now", "soon", "later", "not_now"
    market_readiness: Optional[str] = None  # "ready", "almost", "not_ready"
    market_validation: Optional[Dict[str, Any]] = None  # Market research validation


class WishRequest(BaseModel):
    sources: List[str] = Field(
        default=["reddit", "quora"],
        min_length=1,
        description="Lista de surse (trebuie să conțină cel puțin o sursă)"
    )
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filtre geografice/culturale")
    limit: int = Field(default=100, ge=1, le=1000, description="Număr maxim de wish-uri de colectat")


class WishResponse(BaseModel):
    wishes: List[WishData]
    total: int
    sources_used: List[str]
    processing_time: float
    filters_applied: Optional[Dict[str, Any]] = None


# Complementarity Models
class ComplementarityRequest(BaseModel):
    wish_ids: List[str] = Field(..., min_length=1, description="Lista de ID-uri wish-uri de combinat")
    min_similarity: float = Field(0.6, ge=0.0, le=1.0, description="Similaritate minimă pentru combinare")


class ComplementarityResponse(BaseModel):
    combined_wish: Dict[str, Any]
    source_wishes: List[str]
    similarity_score: float
    combined_at: datetime = Field(default_factory=datetime.now)


# Business Plan Models
class BusinessPlanRequest(BaseModel):
    wish_id: str
    include_financials: bool = True
    include_market_analysis: bool = True


class BusinessPlanResponse(BaseModel):
    id: str
    wish_id: str
    executive_summary: Dict[str, Any]
    market_analysis: Dict[str, Any]
    product_description: Dict[str, Any]
    business_model: Dict[str, Any]
    go_to_market: Dict[str, Any]
    financial_projections: Dict[str, Any]
    implementation_plan: Dict[str, Any]
    generated_at: datetime


# MVP Models
class MVPRequest(BaseModel):
    wish_id: str
    business_plan_id: Optional[str] = None
    tech_stack: Optional[List[str]] = None


class MVPResponse(BaseModel):
    id: str
    wish_id: str
    structure: Dict[str, Any]
    files: List[Dict[str, Any]]
    generated_at: datetime


# Product Gap Models (NOU)
class ProductGapRequest(BaseModel):
    category: str = Field(..., min_length=1, description="Categoria produsului (ex: 'laptop', 'căști')")
    max_price: Optional[float] = Field(None, ge=0, description="Preț maxim dorit (lei)")
    search_volume: Optional[bool] = Field(False, description="Include volum căutări (Google Trends)")


class ProductGap(BaseModel):
    product_name: str
    category: str
    emag_status: str  # "missing", "expensive", "available"
    emag_price: Optional[float] = None
    emag_url: Optional[str] = None
    amazon_uk_price: Optional[float] = None
    amazon_uk_url: Optional[str] = None
    amazon_global_price: Optional[float] = None
    amazon_global_url: Optional[str] = None
    profit_margin: Optional[float] = None  # %
    search_volume: Optional[int] = None
    fba_eligible: bool = False
    risk_level: str = "medium"  # "low", "medium", "high"
    image_url: Optional[str] = None


class FBACalculationRequest(BaseModel):
    amazon_price: float = Field(..., ge=0, description="Preț Amazon (lei)")
    import_costs: float = Field(0, ge=0, description="Costuri import (lei)")
    fba_costs: float = Field(0, ge=0, description="Costuri FBA (lei)")
    selling_price: float = Field(..., ge=0, description="Preț vânzare estimat (lei)")
    quantity: int = Field(1, ge=1, description="Cantitate")


class FBAAnalysis(BaseModel):
    profit_brut: float
    profit_net: float
    roi: float  # %
    break_even_units: int
    risk_level: str
    recommendation: str


class ProductGapResponse(BaseModel):
    gaps: List[ProductGap]
    total_found: int
    search_params: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)
