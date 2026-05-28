import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from app.scrapers.base import BaseScraper

class BigSaveScraper(BaseScraper):
    def __init__(self):
        super().__init__("Big Save Cash & Carry")
        self.target_url = "https://bigsave.co.za/shop/"

    def scrape(self):
        print(f"[{self.supplier_name}] Starting extraction via Playwright + Gemini AI...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Use a standard user agent
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                
                print(f"[{self.supplier_name}] Navigating to {self.target_url}...")
                page.goto(self.target_url, wait_until="networkidle", timeout=30000)
                
                # Give it a second just to render any delayed components
                page.wait_for_timeout(2000)
                
                html_content = page.content()
                browser.close()
            
            # Use BeautifulSoup just to quickly strip scripts and styles before sending to Gemini
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "svg"]):
                tag.decompose()
                
            clean_html = soup.get_text(separator=" ", strip=True)
            
            # Pass the raw cleaned text to Gemini for extraction
            ai_extracted_data = self.ai_engine.extract_products_from_html(clean_html, self.supplier_name)
            
            if ai_extracted_data:
                self.scraped_data = ai_extracted_data
                print(f"[{self.supplier_name}] Successfully extracted {len(self.scraped_data)} items via AI.")
            else:
                print(f"[{self.supplier_name}] AI extracted 0 items total.")
                
        except Exception as e:
            print(f"[{self.supplier_name}] Exception during Playwright extraction: {e}")
