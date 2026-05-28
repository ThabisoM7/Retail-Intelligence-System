import json
import google.generativeai as genai
from app.core.config import settings
from typing import List, Dict
class RetailAIModel:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-3.5-flash as it's fast and supports JSON mode
            self.model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})
        else:
            self.model = None

    def generate_recommendation(self, request_type: str, budget: float, preferences: list[str], retail_data: list[dict], wholesale_data: list[dict] = None) -> dict:
        if not self.model:
            print("WARNING: GEMINI_API_KEY is not set. Returning static mock response.")
            return self._get_fallback_mock(request_type)

        system_prompt, user_prompt = self._build_prompt(request_type, budget, preferences, retail_data, wholesale_data)
        
        try:
            # Gemini chat/generate_content supports passing multiple strings to act as prompt context
            response = self.model.generate_content(
                f"{system_prompt}\n\n{user_prompt}"
            )
            
            content = response.text
            parsed_json = json.loads(content)
            return parsed_json
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._get_fallback_mock(request_type)

    def _build_prompt(self, request_type: str, budget: float, preferences: list[str], retail_data: list[dict], wholesale_data: list[dict]):
        if request_type == "budget_optimizer":
            system_prompt = (
                "You are an AI Retail Assistant optimizing a consumer's shopping basket in South Africa. "
                "You are given a list of available items from local supermarkets and Spaza shops. "
                "Build a Hybrid Basket that stays strictly under the budget. "
                "IMPORTANT: You must return a JSON object containing 'total_calculated_spend', 'remaining_budget', and an 'optimized_basket' array. "
                "Each item in the array must have: item_name, category, source_type, vendor_name, price_zar, deal_type."
            )
            data_context = f"Budget: R{budget}\nTarget Items/Preferences: {preferences}\nAvailable Retail Data: {json.dumps(retail_data)}"
            
        elif request_type == "deal_bundles":
            system_prompt = (
                "You are an AI Deal Analyst for South African consumers. "
                "Group the available items into logical bundles (e.g., 'Breakfast Combo', 'Monthly Staples'). "
                "IMPORTANT: You must return a JSON object containing 'total_calculated_spend', 'remaining_budget', and an 'optimized_basket' array representing these bundles. "
                "Each item in the array must have: item_name (can be a combo name), category, source_type, vendor_name, price_zar (total for combo), deal_type."
            )
            data_context = f"Budget: R{budget}\nTarget Items: {preferences}\nAvailable Retail Data: {json.dumps(retail_data)}"
            
        elif request_type == "sme_intelligence":
            system_prompt = (
                "You are an AI Wholesale Margin Strategist for SME Spaza shop owners in South Africa. "
                "The SME has provided their monthly restocking budget. Your goal is to advise them on how to allocate this budget across wholesale items to maximize ROI. "
                "Compare the Wholesale Cost against Supermarket Retail Prices. "
                "Suggest 'Combos' the SME can sell to maximize margin while undercutting the supermarkets. "
                "IMPORTANT: You must return a JSON object containing a 'suggested_combos' array. "
                "Each item must have: combo_name, included_items (array of strings), suggested_selling_price_zar, competitor_comparison, rationale."
            )
            data_context = f"SME Monthly Restocking Budget: R{budget}\nWholesale Data (Where they buy): {json.dumps(wholesale_data)}\nSupermarket Competitor Data: {json.dumps(retail_data)}"
            
        else:
            system_prompt = "Return empty JSON: {}"
            data_context = ""

        user_prompt = f"Generate recommendations based on this data:\n{data_context}"
        return system_prompt, user_prompt

    def _get_fallback_mock(self, request_type: str) -> dict:
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
                        "deal_type": "Loss Leader Promo"
                    },
                    {
                        "item_name": "Large Eggs 30 Pack",
                        "category": "Fresh Produce",
                        "source_type": "informal_sme",
                        "vendor_name": "Mama Spaza Hub",
                        "price_zar": 74.99,
                        "deal_type": "Localized SME Match"
                    }
                ]
            }
        elif request_type == "deal_bundles":
             return {
                "total_calculated_spend": 150.00,
                "remaining_budget": 350.00,
                "optimized_basket": [
                    {
                        "item_name": "Breakfast Starter Pack (Bread + Eggs + Milk)",
                        "category": "Bundle",
                        "source_type": "informal_sme",
                        "vendor_name": "Sipho's Tuckshop",
                        "price_zar": 125.00,
                        "deal_type": "Spaza Combo"
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
                        "competitor_comparison": "Shoprite sells these separately for R150+. Wholesale cost is R110. You make R30 margin while being R10 cheaper.",
                        "rationale": "High velocity staples purchased together on weekends."
                    }
                ]
            }
        return {}

    def extract_products_from_html(self, raw_text: str, supplier: str) -> list[dict]:
        """
        Uses Gemini to extract a list of products and bulk prices directly from raw HTML or text.
        """
        if not self.model:
            print("WARNING: GEMINI_API_KEY is not set. Returning empty extraction.")
            return []
            
        system_prompt = (
            f"You are an expert retail data extraction AI. Extract all wholesale products and their prices from the following text/HTML for {supplier}. "
            "Return a strictly formatted JSON array of objects. "
            "Each object MUST have the following keys:\n"
            "1. 'item' (string name of the product)\n"
            "2. 'bulk_price' (float, the price in ZAR)\n"
            "3. 'estimated_markup_potential' (string, e.g. '15%')\n"
            "4. 'category' (string, dynamically infer the product's category. For example: 'Food', 'Beverage', 'Utility', 'Toiletries', 'Staples', 'Snacks', etc.)\n"
            "Ignore navigation links, footers, and non-product information."
        )
        
        # To avoid massive token limits, we might truncate if it's absurdly large,
        # but Gemini 1.5 Flash handles 1M tokens easily.
        # We'll truncate to ~100,000 characters just to be safe for API costs.
        truncated_text = raw_text[:100000]
        
        try:
            response = self.model.generate_content(
                f"{system_prompt}\n\nCONTENT TO EXTRACT:\n{truncated_text}"
            )
            
            content = response.text
            # If the model wraps it in markdown block, strip it
            if content.startswith("```json"):
                content = content.strip("`").replace("json\n", "", 1)
            
            parsed_json = json.loads(content)
            
            # Ensure it's a list
            if isinstance(parsed_json, list):
                return parsed_json
            elif isinstance(parsed_json, dict) and "products" in parsed_json:
                return parsed_json["products"]
            return []
            
        except Exception as e:
            print(f"AI Engine Exception during extraction for {supplier}: {e}")
            return []

    def extract_products_from_local_pdf(self, file_path: str, supplier: str, is_retail: bool) -> List[Dict]:
        print(f"[{supplier}] Uploading local PDF {file_path} to Gemini for visual reasoning...")
        try:
            sample_file = genai.upload_file(path=file_path, display_name=f"{supplier} Specials")
            
            if is_retail:
                # Retail Supermarket Schema
                system_prompt = (
                    f"You are an expert retail data extraction AI. Extract all products and their prices from the following PDF catalog for {supplier}. "
                    "Return a strictly formatted JSON array of objects. "
                    "Each object MUST have the following keys:\n"
                    "1. 'item' (string name of the product)\n"
                    "2. 'price' (float, the price in ZAR)\n"
                    "3. 'category' (string, e.g. 'Food', 'Beverage', 'Utility', 'Toiletries', 'Staples')\n"
                    "4. 'deal_expiry' (string, e.g. '2023-12-31' or 'Unknown' if not visible)\n"
                    "5. 'loss_leader_flag' (boolean, set to true if it seems like a heavily discounted promotion designed to get people into the store)\n"
                    "Ignore navigation links, footers, and non-product information. If you cannot find any products, return an empty array []."
                )
            else:
                # Wholesale Schema
                system_prompt = (
                    f"You are an expert retail data extraction AI. Extract all wholesale products and their prices from the following PDF catalog for {supplier}. "
                    "Return a strictly formatted JSON array of objects. "
                    "Each object MUST have the following keys:\n"
                    "1. 'item' (string name of the product)\n"
                    "2. 'bulk_price' (float, the price in ZAR for the bulk pack)\n"
                    "3. 'unit_price' (float, calculate the price per single unit if a bulk quantity is mentioned, otherwise same as bulk_price)\n"
                    "4. 'bulk_quantity_savings' (string, e.g. 'Save R15 on a case of 6')\n"
                    "5. 'category' (string, e.g. 'Food', 'Beverage', 'Utility', 'Toiletries', 'Staples')\n"
                    "Ignore navigation links, footers, and non-product information. If you cannot find any products, return an empty array []."
                )
            
            print(f"[{supplier}] Running visual extraction...")
            response = self.model.generate_content([system_prompt, sample_file])
            
            # Clean up immediately
            genai.delete_file(sample_file.name)
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            data = json.loads(raw_text)
            
            if isinstance(data, list):
                # Ensure all products have the required fields
                for item in data:
                    if 'category' not in item:
                        item['category'] = "Uncategorized"
                return data
            return []
            
        except Exception as e:
            print(f"AI Engine Exception during local PDF extraction for {supplier}: {e}")
            try:
                if 'sample_file' in locals():
                    genai.delete_file(sample_file.name)
            except:
                pass
            return []
