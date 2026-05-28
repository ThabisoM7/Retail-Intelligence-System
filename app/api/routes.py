from fastapi import APIRouter, Depends
from app.api.models import RecommendRequest, RecommendationResponse
from app.api.auth import get_api_key
from app.services.data_layer import get_corporate_specials, get_sme_inventory
from app.services.db_layer import get_wholesale_prices
from app.services.ai_engine import RetailAIModel

router = APIRouter()
ai_model = RetailAIModel()

@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendRequest, api_key: str = Depends(get_api_key)):
    request_type = request.request_type
    location = request.location.model_dump()
    
    try:
        # 1. Fetch relevant Data
        corporate_data = get_corporate_specials(location)
        sme_inventory = get_sme_inventory(location)
        combined_retail_data = corporate_data + sme_inventory
        
        wholesale_data = None
        
        # 2. Strict Boundary: Only fetch Wholesale Data if user is Premium SME requesting sme_intelligence
        if request_type == "sme_intelligence" and request.is_premium:
            wholesale_data = get_wholesale_prices(location, request.preferences)
            
        # 3. Call AI Recommendation Engine
        ai_response = ai_model.generate_recommendation(
            request_type=request_type,
            budget=request.budget or 0.0,
            preferences=request.preferences,
            retail_data=combined_retail_data,
            wholesale_data=wholesale_data,
            vendor_inventory=request.vendor_inventory
        )
        
        # Build final response based on AI output
        return RecommendationResponse(
            status="success",
            ris_mode="live_overpass_v1",
            total_calculated_spend=ai_response.get("total_calculated_spend"),
            remaining_budget=ai_response.get("remaining_budget"),
            optimized_basket=ai_response.get("optimized_basket"),
            suggested_combos=ai_response.get("suggested_combos")
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)} \nTrace: {error_details}")
