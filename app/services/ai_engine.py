import json
import google.generativeai as genai
from app.core.config import settings

class RetailAIModel:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-1.5-flash as it's fast and supports JSON mode
            self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
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
