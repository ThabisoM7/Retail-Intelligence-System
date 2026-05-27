from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    try:
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
    return None

def get_wholesale_prices(location: dict, preferences: list[str]) -> list[dict]:
    """
    STRICTLY FOR SMEs. Retrieves cached wholesale data scraped from distributors.
    """
    supabase = get_supabase_client()
    if not supabase:
        print("Fallback to mock wholesale data due to missing Supabase connection.")
        return get_mock_wholesale()
    
    try:
        # Fetching wholesale data via Supabase Python SDK
        response = supabase.table("wholesale_inventory").select("supplier, item, bulk_price, estimated_markup_potential").limit(20).execute()
        
        if response.data:
            return response.data
        else:
            print("Supabase returned no data. Using fallback.")
            return get_mock_wholesale()
            
    except Exception as e:
        print(f"Error querying wholesale prices via Supabase: {e}")
        return get_mock_wholesale()

def get_mock_wholesale() -> list[dict]:
    return [
        {"supplier": "Kit Kat Cash & Carry", "item": "Cooking Oil 2L (Box of 6)", "bulk_price": 420.00, "estimated_markup_potential": "22%"},
        {"supplier": "Kit Kat Cash & Carry", "item": "Maize Meal 10kg (Bale of 5)", "bulk_price": 350.00, "estimated_markup_potential": "18%"},
        {"supplier": "Redstar Wholesale", "item": "White Bread (Crate of 10)", "bulk_price": 120.00, "estimated_markup_potential": "30%"},
        {"supplier": "Big Save", "item": "Milk 1L (Case of 6)", "bulk_price": 130.00, "estimated_markup_potential": "25%"},
    ]
