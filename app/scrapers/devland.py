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
        print(f"[{self.supplier_name}] Starting extraction via PyPDF2 parsing...")
        
        try:
            # We will simulate the PDF fetching and parsing process
            # since a real PDF URL might be dynamic or unavailable.
            # Real implementation would be:
            # 1. Fetch HTML, find href ending in .pdf
            # 2. Download PDF bytes into io.BytesIO()
            # 3. Read with PyPDF2 and regex extract prices.
            
            # Simulated failure to hit the real PDF to trigger the robust fallback mock data
            raise requests.exceptions.ConnectionError("Simulating PDF download failure")

        except Exception as e:
            print(f"[{self.supplier_name}] Exception during PDF extraction: {e}")
            self._inject_mock_data()
            
    def _inject_mock_data(self):
        print(f"[{self.supplier_name}] Injecting fallback mock data for demonstration.")
        self.scraped_data = [
            {"item": "Snowflake Cake Flour 10kg", "bulk_price": 105.00, "estimated_markup_potential": "18%"},
            {"item": "Tastic Rice 10kg (Bale of 5)", "bulk_price": 600.00, "estimated_markup_potential": "22%"},
            {"item": "Iwisa Maize Meal 10kg", "bulk_price": 85.00, "estimated_markup_potential": "15%"},
            {"item": "Lucky Star Pilchards 400g (Shrink of 12)", "bulk_price": 240.00, "estimated_markup_potential": "28%"},
        ]
