import time
import re
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class KitKatScraper(BaseScraper):
    def __init__(self):
        super().__init__("Kit Kat Cash & Carry")
        self.base_url = "https://www.kitkatgroup.com/shop/"
        self.categories = ["groceries", "toiletries"]

    def scrape(self):
        logger.info(f"[{self.supplier_name}] Starting extraction via Playwright + BeautifulSoup (Zero AI Cost)...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                
                for category in self.categories:
                    for page_num in range(1, 4):
                        url = f"{self.base_url}{category}?page={page_num}"
                        logger.info(f"[{self.supplier_name}] Navigating to {url}...")
                        
                        try:
                            page.goto(url, wait_until="networkidle", timeout=30000)
                            page.wait_for_timeout(2000)
                            
                            html_content = page.content()
                            if "No products found" in html_content or "no-products" in html_content:
                                logger.info(f"[{self.supplier_name}] Reached end of category {category} at page {page_num}.")
                                break
                            
                            soup = BeautifulSoup(html_content, "html.parser")
                            
                            # Heuristic: Find all product container-like divs
                            # Usually they have classes like 'product', 'item', 'card'
                            product_containers = soup.find_all(['div', 'li'], class_=re.compile(r'(product|item|card|col-)', re.I))
                            
                            extracted_count = 0
                            for container in product_containers:
                                text_content = container.get_text(separator=" ", strip=True)
                                
                                # Look for a price pattern
                                price_match = re.search(r'(?:R|ZAR)\s*(\d+(?:[.,]\d{2})?)', text_content, re.I)
                                if not price_match:
                                    continue
                                    
                                # Find an image
                                img_tag = container.find('img')
                                img_url = img_tag.get('src') if img_tag else None
                                
                                # Heuristic item name (longest text string in the container that isn't the price)
                                strings = [s.strip() for s in container.stripped_strings if len(s.strip()) > 3]
                                item_name = strings[0] if strings else "Unknown Product"
                                
                                price_val = float(price_match.group(1).replace(',', '.'))
                                
                                self.scraped_data.append({
                                    "item": item_name,
                                    "bulk_price": price_val,
                                    "estimated_markup_potential": "15%", # Default estimate
                                    "category": category.capitalize(),
                                    "image_url": img_url
                                })
                                extracted_count += 1
                                
                            if extracted_count > 0:
                                logger.info(f"[{self.supplier_name}] Successfully extracted {extracted_count} items from {category} page {page_num} via BS4.")
                            else:
                                logger.info(f"[{self.supplier_name}] No items extracted from {category} page {page_num}. Ending pagination for this category.")
                                break
                                
                        except Exception as cat_e:
                            logger.error(f"[{self.supplier_name}] Failed to scrape {category} page {page_num}: {cat_e}", exc_info=True)
                            break
                        
                browser.close()
            
        except Exception as e:
            logger.error(f"[{self.supplier_name}] Exception during scraping: {e}", exc_info=True)
