from app.services.location_service import get_nearby_supermarkets

def get_corporate_specials(location: dict) -> list[dict]:
    # 1. Get real supermarket locations nearby using Overpass API
    nearby_stores = get_nearby_supermarkets(location['lat'], location['lng'])
    
    specials = []
    # 2. Attach mock specials to these real locations based on brand
    for store in nearby_stores:
        brand = store.get("brand", "").lower()
        store_name = store.get("name")
        
        if "shoprite" in brand:
            specials.append({"store": store_name, "item": "10kg Super Sun Maize Meal", "price": 135.00, "category": "Wholesale Staples", "type": "formal_retail"})
            specials.append({"store": store_name, "item": "2L Sunflower Oil", "price": 45.99, "category": "Wholesale Staples", "type": "formal_retail"})
        elif "pick n pay" in brand or "picknpay" in brand:
            specials.append({"store": store_name, "item": "White Bread", "price": 16.99, "category": "Wholesale Staples", "type": "formal_retail"})
            specials.append({"store": store_name, "item": "2L Milk", "price": 28.50, "category": "Dairy", "type": "formal_retail"})
        elif "checkers" in brand:
            specials.append({"store": store_name, "item": "Large Eggs 30 Pack", "price": 75.00, "category": "Fresh Produce", "type": "formal_retail"})
            specials.append({"store": store_name, "item": "10kg Rice", "price": 145.00, "category": "Wholesale Staples", "type": "formal_retail"})
        else:
            # Generic
            specials.append({"store": store_name, "item": "Mixed Vegetables 1kg", "price": 35.00, "category": "Fresh Produce", "type": "formal_retail"})
            
    return specials

def get_sme_inventory(location: dict) -> list[dict]:
    # Mocked local spaza shops (Informal SMEs)
    return [
        {"store": "Mama Spaza Hub", "item": "5kg Maize Meal", "price": 65.00, "category": "Wholesale Staples", "type": "informal_sme"},
        {"store": "Mama Spaza Hub", "item": "Large Eggs 30 Pack", "price": 74.99, "category": "Fresh Produce", "type": "informal_sme"},
        {"store": "Sipho's Tuckshop", "item": "2L Milk", "price": 32.00, "category": "Dairy", "type": "informal_sme"},
        {"store": "Sipho's Tuckshop", "item": "White Bread", "price": 18.00, "category": "Wholesale Staples", "type": "informal_sme"},
    ]
