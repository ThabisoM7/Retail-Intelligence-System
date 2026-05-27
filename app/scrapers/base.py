from typing import List, Dict
from supabase import create_client, Client
from app.core.config import settings

class BaseScraper:
    def __init__(self, supplier_name: str):
        self.supplier_name = supplier_name
        self.scraped_data: List[Dict] = []
        
        try:
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            print(f"[{self.supplier_name}] Error initializing Supabase client: {e}")
            self.supabase = None

    def scrape(self):
        """Implement the scraping logic in subclasses to populate self.scraped_data"""
        raise NotImplementedError

    def save_to_db(self):
        """Save self.scraped_data to Supabase via REST API"""
        if not self.scraped_data:
            print(f"[{self.supplier_name}] No data to save.")
            return
            
        if not self.supabase:
            print(f"[{self.supplier_name}] Cannot save to Supabase: Client not initialized (Check env variables).")
            return

        print(f"[{self.supplier_name}] Saving {len(self.scraped_data)} items to Supabase...")
        
        try:
            records_to_insert = [
                {
                    "supplier": self.supplier_name,
                    "item": item.get("item", "Unknown"),
                    "bulk_price": item.get("bulk_price", 0.0),
                    "estimated_markup_potential": item.get("estimated_markup_potential", "15%")
                }
                for item in self.scraped_data
            ]
            
            # Using Supabase native bulk insert via REST
            response = self.supabase.table("wholesale_inventory").insert(records_to_insert).execute()
            
            print(f"[{self.supplier_name}] Successfully saved to database.")
            
        except Exception as e:
            print(f"[{self.supplier_name}] Database error: {e}")
