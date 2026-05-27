from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Location(BaseModel):
    lat: float
    lng: float

class RecommendRequest(BaseModel):
    user_id: str
    request_type: Literal["budget_optimizer", "deal_bundles", "sme_intelligence"]
    is_premium: bool = False
    budget: Optional[float] = None
    timeframe: Optional[str] = "next 2 weeks"
    location: Location
    preferences: List[str]

class OptimizedBasketItem(BaseModel):
    item_name: str
    category: str
    source_type: Literal["formal_retail", "informal_sme", "wholesale_supplier"]
    vendor_name: str
    price_zar: float
    deal_type: str

class SMESuggestedCombo(BaseModel):
    combo_name: str
    included_items: List[str]
    suggested_selling_price_zar: float
    competitor_comparison: str
    rationale: str

class RecommendationResponse(BaseModel):
    status: str = "success"
    ris_mode: str = "live_overpass_v1"
    total_calculated_spend: Optional[float] = None
    remaining_budget: Optional[float] = None
    optimized_basket: Optional[List[OptimizedBasketItem]] = None
    suggested_combos: Optional[List[SMESuggestedCombo]] = None
