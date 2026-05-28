from app.services.location_service import get_nearby_supermarkets

def get_corporate_specials(location: dict) -> list[dict]:
    # 1. Get real supermarket locations nearby using Overpass API
    nearby_stores = get_nearby_supermarkets(location['lat'], location['lng'])
    
    # 2. Fetch all retail specials from Supabase for this region
    import requests
    from app.core.config import settings
    
    specials = []
    
    if not settings.SUPABASE_URL:
        print("Missing Supabase credentials, returning empty specials.")
        return []
        
    url = f"{settings.SUPABASE_URL}/rest/v1/retail_inventory?select=*"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            db_specials = response.json()
            
            # 3. Attach real specials to the physical locations nearby
            for store in nearby_stores:
                brand = store.get("brand", "").lower()
                store_name = store.get("name")
                
                # Find specials matching this brand
                matching_specials = [s for s in db_specials if s.get("brand", "").lower() in brand or brand in s.get("brand", "").lower()]
                
                for s in matching_specials:
                    specials.append({
                        "store": store_name,
                        "item": s.get("item", ""),
                        "price": s.get("price", 0.0),
                        "category": s.get("category", ""),
                        "type": s.get("type", "formal_retail")
                    })
    except Exception as e:
        print(f"Failed to query retail_inventory: {e}")
        
    return specials

def get_sme_inventory(location: dict) -> list[dict]:
    # Mocked local spaza shops (Informal SMEs)
    return [
        {"store": "Mama Spaza Hub", "item": "5kg Maize Meal", "price": 65.00, "category": "Wholesale Staples", "type": "informal_sme"},
        {"store": "Mama Spaza Hub", "item": "Large Eggs 30 Pack", "price": 74.99, "category": "Fresh Produce", "type": "informal_sme"},
        {"store": "Sipho's Tuckshop", "item": "2L Milk", "price": 32.00, "category": "Dairy", "type": "informal_sme"},
        {"store": "Sipho's Tuckshop", "item": "White Bread", "price": 18.00, "category": "Wholesale Staples", "type": "informal_sme"},
    ]
