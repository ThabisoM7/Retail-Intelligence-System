import logging
from app.services.location_service import get_nearby_supermarkets
from app.services.db_layer import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_corporate_specials(location: dict) -> list[dict]:
    # 1. Get real supermarket locations nearby using Overpass API
    nearby_stores = get_nearby_supermarkets(location['lat'], location['lng'])
    if not nearby_stores:
        return []
    
    # 2. Fetch all retail specials from Supabase for this region/national
    supabase = get_supabase_client()
    db_specials = []
    
    if supabase:
        try:
            response = supabase.table("retail_inventory").select("*").execute()
            db_specials = response.data or []
        except Exception as e:
            logger.error(f"Failed to query retail_inventory via Supabase: {e}", exc_info=True)
    else:
        if not settings.MOCK_MODE:
            raise Exception("Supabase connection failed and MOCK_MODE is False.")
        logger.warning("Missing Supabase credentials, returning empty specials.")
        return []
    
    specials = []
    # 3. National Association Logic: Attach real specials to the physical locations nearby
    for store in nearby_stores:
        brand = store.get("brand", "").lower()
        store_name = store.get("name")
        
        # Find specials matching this brand. Since 1 leaflet (e.g. "SPAR") applies to all, we do a substring match.
        matching_specials = [s for s in db_specials if s.get("brand", "").lower() in brand or brand in s.get("brand", "").lower()]
        
        for s in matching_specials:
            specials.append({
                "store": store_name,
                "item": s.get("item", ""),
                "price": float(s.get("price", 0.0)) if s.get("price") else 0.0,
                "category": s.get("category", ""),
                "type": s.get("type", "formal_retail"),
                "image_url": s.get("image_url", None)
            })
            
    return specials

def get_sme_inventory(location: dict) -> list[dict]:
    if settings.MOCK_MODE:
        # Mocked local spaza shops (Informal SMEs)
        return [
            {"store": "Mama Spaza Hub", "item": "5kg Maize Meal", "price": 65.00, "category": "Wholesale Staples", "type": "informal_sme"},
            {"store": "Mama Spaza Hub", "item": "Large Eggs 30 Pack", "price": 74.99, "category": "Fresh Produce", "type": "informal_sme"},
            {"store": "Sipho's Tuckshop", "item": "2L Milk", "price": 32.00, "category": "Dairy", "type": "informal_sme"},
            {"store": "Sipho's Tuckshop", "item": "White Bread", "price": 18.00, "category": "Wholesale Staples", "type": "informal_sme"},
        ]
    return []

