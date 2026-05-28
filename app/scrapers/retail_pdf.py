import requests
from app.scrapers.base import BaseScraper
from app.core.config import settings

class ShopriteScraper(BaseScraper):
    def __init__(self):
        # We pass table_name="retail_inventory" to save to the new retail table
        super().__init__("Shoprite", table_name="retail_inventory")
        # In a real environment, this would be uploaded by an Admin.
        # For the Hackathon MVP, we use a regional baseline PDF.
        # (This is a sample Guzzle-like PDF URL for demonstration)
        self.target_url = "https://files.sitebuilder.1-grid.com/ba/dd/baddd098-49d8-4c3c-a6c7-37fd19cecb52.pdf" 
        
    def scrape(self):
        print(f"[{self.supplier_name}] Starting extraction via Native PDF parsing (Gauteng Region)...")
        try:
            ai_extracted_data = self.ai_engine.extract_products_from_pdf_url(self.target_url, self.supplier_name)
            
            if ai_extracted_data:
                # Add the 'region' and 'type' keys to match the retail schema
                for item in ai_extracted_data:
                    item['region'] = "Gauteng"
                    item['type'] = "formal_retail"
                    item['price'] = item.pop('bulk_price', 0.0) # rename bulk_price to price
                    
                self.scraped_data = ai_extracted_data
                print(f"[{self.supplier_name}] Successfully extracted {len(self.scraped_data)} items via AI PDF Reasoning.")
            else:
                print(f"[{self.supplier_name}] AI extracted 0 items from PDF.")

        except Exception as e:
            print(f"[{self.supplier_name}] Exception during PDF extraction: {e}")
            
class SparScraper(BaseScraper):
    def __init__(self):
        super().__init__("Spar", table_name="retail_inventory")
        # Using the same demo PDF for the hackathon MVP to prove the concept works
        self.target_url = "https://files.sitebuilder.1-grid.com/ba/dd/baddd098-49d8-4c3c-a6c7-37fd19cecb52.pdf"
        
    def scrape(self):
        print(f"[{self.supplier_name}] Starting extraction via Native PDF parsing (Gauteng Region)...")
        try:
            ai_extracted_data = self.ai_engine.extract_products_from_pdf_url(self.target_url, self.supplier_name)
            
            if ai_extracted_data:
                for item in ai_extracted_data:
                    item['region'] = "Gauteng"
                    item['type'] = "formal_retail"
                    item['price'] = item.pop('bulk_price', 0.0)
                    
                self.scraped_data = ai_extracted_data
                print(f"[{self.supplier_name}] Successfully extracted {len(self.scraped_data)} items via AI PDF Reasoning.")
            else:
                print(f"[{self.supplier_name}] AI extracted 0 items from PDF.")

        except Exception as e:
            print(f"[{self.supplier_name}] Exception during PDF extraction: {e}")
