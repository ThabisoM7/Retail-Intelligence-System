from typing import List, Dict
import requests
from app.core.config import settings
from app.services.ai_engine import RetailAIModel

class BaseScraper:
    def __init__(self, supplier_name: str, table_name: str = "wholesale_inventory"):
        self.supplier_name = supplier_name
        self.scraped_data: List[Dict] = []
        self.ai_engine = RetailAIModel()
        self.supabase_url = f"{settings.SUPABASE_URL}/rest/v1/{table_name}"
        self.supabase_headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def scrape(self):
        """Implement the scraping logic in subclasses to populate self.scraped_data"""
        raise NotImplementedError

    def save_to_db(self):
        """Save self.scraped_data to Supabase via raw REST API"""
        if not self.scraped_data:
            print(f"[{self.supplier_name}] No data to save.")
            return
            
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            print(f"[{self.supplier_name}] Cannot save to Supabase: Missing credentials.")
            return

        print(f"[{self.supplier_name}] Saving {len(self.scraped_data)} items to Supabase...")
        
        try:
            records_to_insert = []
            for item in self.scraped_data:
                record = item.copy()
                # Determine which table schema we are targeting
                if "wholesale_inventory" in self.supabase_url:
                    record["supplier"] = self.supplier_name
                    if "estimated_markup_potential" not in record:
                        record["estimated_markup_potential"] = "15%"
                elif "retail_inventory" in self.supabase_url:
                    record["brand"] = self.supplier_name
                    # Type and Region are usually injected by the Retail scraper, but just in case:
                    if "type" not in record:
                        record["type"] = "formal_retail"
                    
                    # Remove wholesale-specific fields that cause Supabase schema errors
                    record.pop("estimated_markup_potential", None)
                    record.pop("supplier", None)
                
                records_to_insert.append(record)
            
            response = requests.post(self.supabase_url, headers=self.supabase_headers, json=records_to_insert)
            
            if response.status_code in (201, 200, 204):
                print(f"[{self.supplier_name}] Successfully saved to database.")
            else:
                print(f"[{self.supplier_name}] Failed to save. Status: {response.status_code}, Error: {response.text}")
            
        except Exception as e:
            print(f"[{self.supplier_name}] Database request error: {e}")
