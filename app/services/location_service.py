import logging
import requests
from typing import List, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_nearby_supermarkets(lat: float, lng: float, radius: int = 5000) -> List[Dict]:
    """
    Query OpenStreetMap via Overpass API to find supermarkets within `radius` meters
    of the given lat/lng. Filters for specific major South African chains.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query for nodes tagged as supermarket within radius of lat,lng
    overpass_query = f"""
    [out:json];
    (
      node["shop"="supermarket"](around:{radius},{lat},{lng});
      way["shop"="supermarket"](around:{radius},{lat},{lng});
      relation["shop"="supermarket"](around:{radius},{lat},{lng});
    );
    out center;
    """
    
    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        supermarkets = []
        target_brands = ["shoprite", "checkers", "pick n pay", "picknpay", "spar", "boxer"]
        
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name", "Unknown Supermarket")
            brand = tags.get("brand", "")
            
            name_lower = name.lower()
            brand_lower = brand.lower()
            
            # Filter for the specific chains required
            if any(b in name_lower for b in target_brands) or any(b in brand_lower for b in target_brands):
                lat_coord = element.get("lat") or element.get("center", {}).get("lat")
                lon_coord = element.get("lon") or element.get("center", {}).get("lon")
                
                if lat_coord and lon_coord:
                    supermarkets.append({
                        "name": name,
                        "brand": brand if brand else name,
                        "lat": lat_coord,
                        "lng": lon_coord,
                        "source": "OpenStreetMap"
                    })
                    
        # If still empty, provide mocks only if MOCK_MODE is enabled
        if not supermarkets and settings.MOCK_MODE:
            logger.warning("No supermarkets found via Overpass. Using mock data.")
            return get_mock_supermarkets(lat, lng)
            
        return supermarkets

    except Exception as e:
        logger.error(f"Overpass API error: {e}", exc_info=True)
        if settings.MOCK_MODE:
            logger.warning("Falling back to mock data.")
            return get_mock_supermarkets(lat, lng)
        return []

def get_mock_supermarkets(lat: float, lng: float) -> List[Dict]:
    """Fallback mock data if Overpass fails or finds nothing."""
    return [
        {"name": "Shoprite Mamelodi East", "brand": "Shoprite", "lat": lat + 0.01, "lng": lng + 0.01, "source": "Mock"},
        {"name": "Pick n Pay Soshanguve", "brand": "Pick n Pay", "lat": lat - 0.02, "lng": lng + 0.015, "source": "Mock"},
        {"name": "Checkers Menlyn", "brand": "Checkers", "lat": lat + 0.005, "lng": lng - 0.01, "source": "Mock"}
    ]
