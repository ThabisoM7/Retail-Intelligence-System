import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from app.scrapers.base import BaseScraper

class KitKatScraper(BaseScraper):
    def __init__(self):
        super().__init__("Kit Kat Cash & Carry")
        self.base_url = "https://www.kitkatgroup.com/shop/"
        self.categories = ["groceries", "toiletries"]

    def scrape(self):
        print(f"[{self.supplier_name}] Starting extraction via Playwright + Gemini AI...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                
                # We will scrape up to 3 pages per category
                for category in self.categories:
                    for page_num in range(1, 4):
                        url = f"{self.base_url}{category}?page={page_num}"
                        print(f"[{self.supplier_name}] Navigating to {url}...")
                        
                        try:
                            page.goto(url, wait_until="networkidle", timeout=30000)
                            page.wait_for_timeout(2000)
                            
                            html_content = page.content()
                            
                            # Check if the page actually has products or if it's empty/out of bounds
                            if "No products found" in html_content or "no-products" in html_content:
                                print(f"[{self.supplier_name}] Reached end of category {category} at page {page_num}.")
                                break
                            
                            # Strip out heavy scripts/styles
                            soup = BeautifulSoup(html_content, "html.parser")
                            for tag in soup(["script", "style", "nav", "footer", "svg"]):
                                tag.decompose()
                                
                            clean_html = soup.get_text(separator=" ", strip=True)
                            
                            # Pass to Gemini
                            ai_extracted_data = self.ai_engine.extract_products_from_html(clean_html, self.supplier_name)
                            
                            if ai_extracted_data:
                                self.scraped_data.extend(ai_extracted_data)
                                print(f"[{self.supplier_name}] Successfully extracted {len(ai_extracted_data)} items from {category} page {page_num} via AI.")
                            else:
                                print(f"[{self.supplier_name}] No items extracted from {category} page {page_num}. Ending pagination for this category.")
                                break
                                
                        except Exception as cat_e:
                            print(f"[{self.supplier_name}] Failed to scrape {category} page {page_num}: {cat_e}")
                            break
                        
                browser.close()
            
        except Exception as e:
            print(f"[{self.supplier_name}] Exception during scraping: {e}")
