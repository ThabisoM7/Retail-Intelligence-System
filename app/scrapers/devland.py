import requests
import io
import PyPDF2
from app.scrapers.base import BaseScraper
import random
import re

class DevlandScraper(BaseScraper):
    def __init__(self):
        super().__init__("Devland Cash & Carry")
        # In reality, this would first hit the HTML page to find the PDF link
        self.target_url = "https://devland.co.za/monthly-specials"

    def scrape(self):
        print(f"[{self.supplier_name}] Starting extraction via Native PDF parsing...")
        
        try:
            # We will use the exact PDF URL the user provided for testing
            pdf_url = "https://files.sitebuilder.1-grid.com/ba/dd/baddd098-49d8-4c3c-a6c7-37fd19cecb52.pdf"
            
            ai_extracted_data = self.ai_engine.extract_products_from_pdf_url(pdf_url, self.supplier_name)
            
            if ai_extracted_data:
                self.scraped_data = ai_extracted_data
                print(f"[{self.supplier_name}] Successfully extracted {len(self.scraped_data)} items via AI PDF Reasoning.")
            else:
                print(f"[{self.supplier_name}] AI extracted 0 items from PDF.")

        except Exception as e:
            print(f"[{self.supplier_name}] Exception during PDF extraction: {e}")
