import json
import logging
import google.generativeai as genai
from app.core.config import settings
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class RetailAIModel:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
        else:
            self.model = None

    def _parse_robust_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            try:
                return json.loads(text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON output: {e}\nRaw output: {text}")
                return {}

    def generate_recommendation(self, request_type: str, budget: float, preferences: list[str], retail_data: list[dict], wholesale_data: list[dict] = None, vendor_inventory: Optional[List[Dict[str, float]]] = None) -> dict:
        if not self.model:
            logger.warning("GEMINI_API_KEY is not set.")
            return self._get_fallback_mock(request_type)

        system_prompt, user_prompt = self._build_prompt(request_type, budget, preferences, retail_data, wholesale_data, vendor_inventory)
        
        try:
            response = self.model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            return self._parse_robust_json(response.text)
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            return self._get_fallback_mock(request_type)

    def _build_prompt(self, request_type: str, budget: float, preferences: list[str], retail_data: list[dict], wholesale_data: list[dict], vendor_inventory: Optional[List[Dict[str, float]]]):
        if request_type == "budget_optimizer":
            system_prompt = (
                "You are an AI Retail Assistant optimizing a consumer's shopping basket in South Africa. "
                "Build a Hybrid Basket that stays strictly under the budget. "
                "IMPORTANT: Return a JSON object containing 'total_calculated_spend', 'remaining_budget', and an 'optimized_basket' array. "
                "Each item must have: item_name, category, source_type, vendor_name, price_zar, deal_type, and image_url."
            )
            data_context = f"Budget: R{budget}\nPreferences: {preferences}\nRetail Data: {json.dumps(retail_data)}"
            
        elif request_type == "deal_bundles":
            system_prompt = (
                "You are an AI Deal Analyst. Group available items into logical bundles. "
                "Return a JSON object containing 'total_calculated_spend', 'remaining_budget', and 'optimized_basket' array. "
                "Each item must have: item_name (combo name), category, source_type, vendor_name, price_zar, deal_type, image_url."
            )
            data_context = f"Budget: R{budget}\nPreferences: {preferences}\nRetail Data: {json.dumps(retail_data)}"
            
        elif request_type == "sme_intelligence":
            system_prompt = (
                "You are an AI Wholesale Margin Strategist. "
                "Calculate exactly how a Spaza owner can maximize profit. "
            )
            if vendor_inventory:
                system_prompt += (
                    "The vendor has provided their actual inventory cost. Use their provided 'cost_price' as the Wholesale Cost. "
                )
            else:
                 system_prompt += (
                    "Use the provided scraped Wholesale Data to estimate Wholesale Cost. "
                )
            system_prompt += (
                "For Arbitrage: Set 'Suggested Selling Price' to 5% cheaper than the local Supermarket Price. "
                "Calculate 'Assumed Profit' = Suggested Selling Price - Wholesale Cost. "
                "Calculate 'Margin %' = (Assumed Profit / Suggested Selling Price) * 100. "
                "Return a JSON object with 'suggested_combos' array. Each item must have: combo_name, included_items (array of strings), suggested_selling_price_zar, competitor_comparison, rationale, image_url."
            )
            data_context = f"Budget: R{budget}\nWholesale Data: {json.dumps(wholesale_data)}\nSupermarket Competitor Data: {json.dumps(retail_data)}\nVendor Actual Inventory: {json.dumps(vendor_inventory)}"
            
        else:
            system_prompt = "Return empty JSON: {}"
            data_context = ""

        user_prompt = f"Generate recommendations based on this data:\n{data_context}"
        return system_prompt, user_prompt

    def _get_fallback_mock(self, request_type: str) -> dict:
        if not settings.MOCK_MODE:
            return {}
        if request_type == "budget_optimizer":
            return {
                "total_calculated_spend": 209.99,
                "remaining_budget": 290.01,
                "optimized_basket": [
                    {
                        "item_name": "Super Sun Maize Meal 10kg",
                        "category": "Wholesale Staples",
                        "source_type": "formal_retail",
                        "vendor_name": "Shoprite Mamelodi East",
                        "price_zar": 135.00,
                        "deal_type": "Loss Leader Promo",
                        "image_url": "https://example.com/maize.jpg"
                    }
                ]
            }
        elif request_type == "sme_intelligence":
             return {
                "suggested_combos": [
                    {
                        "combo_name": "Weekend Fry-Up Special",
                        "included_items": ["2L Sunflower Oil", "Large Eggs 30 Pack", "White Bread"],
                        "suggested_selling_price_zar": 140.00,
                        "competitor_comparison": "Shoprite sells these separately for R150+. Wholesale cost is R110. Margin: 21%.",
                        "rationale": "High velocity staples.",
                        "image_url": "https://example.com/eggs.jpg"
                    }
                ]
            }
        return {}

    def extract_products_from_html(self, raw_text: str, supplier: str) -> list[dict]:
        # DEPRECATED: We are moving to BeautifulSoup for HTML scraping to save tokens.
        # This remains here if AI parsing is still desired.
        if not self.model:
            return []
        system_prompt = (
            f"Extract wholesale products from {supplier}. Return JSON array with keys: 'item', 'bulk_price', 'estimated_markup_potential', 'category', 'image_url'."
        )
        try:
            response = self.model.generate_content(f"{system_prompt}\n\nCONTENT:\n{raw_text[:100000]}")
            data = self._parse_robust_json(response.text)
            if isinstance(data, list): return data
            if isinstance(data, dict) and "products" in data: return data["products"]
            return []
        except Exception as e:
            logger.error(f"HTML extraction error: {e}")
            return []

    def _fetch_image_from_ddg(self, query: str) -> Optional[str]:
        """Silently fetch a generic product image using DuckDuckGo."""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(query, max_results=1))
                if results:
                    return results[0].get('image')
        except Exception as e:
            logger.debug(f"DDGS Image fetch failed for '{query}': {e}")
        return None

    def extract_products_from_local_pdf(self, file_path: str, supplier: str, is_retail: bool) -> List[Dict]:
        logger.info(f"[{supplier}] Uploading local PDF {file_path} to Gemini for visual reasoning...")
        try:
            sample_file = genai.upload_file(path=file_path, display_name=f"{supplier} Specials")
            
            if is_retail:
                system_prompt = (
                    f"Extract products from PDF for {supplier}. Return JSON array of objects with keys: "
                    "'item', 'price', 'category', 'deal_expiry', 'loss_leader_flag'."
                )
            else:
                system_prompt = (
                    f"Extract wholesale products from PDF for {supplier}. Return JSON array of objects with keys: "
                    "'item', 'bulk_price', 'unit_price', 'bulk_quantity_savings', 'category'."
                )
            
            response = self.model.generate_content([system_prompt, sample_file])
            genai.delete_file(sample_file.name)
            
            data = self._parse_robust_json(response.text)
            
            if isinstance(data, list):
                for item in data:
                    if 'category' not in item:
                        item['category'] = "Uncategorized"
                    # Run DDG Image Search for the extracted PDF item
                    item_name = item.get("item", "")
                    if item_name:
                        image_url = self._fetch_image_from_ddg(f"{supplier} {item_name} product south africa")
                        item["image_url"] = image_url
                return data
            return []
            
        except Exception as e:
            logger.error(f"AI Engine Exception during local PDF extraction for {supplier}: {e}", exc_info=True)
            try:
                if 'sample_file' in locals():
                    genai.delete_file(sample_file.name)
            except:
                pass
            return []
