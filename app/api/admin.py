import os
import shutil
import uuid
import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.services.ai_engine import RetailAIModel
from app.core.config import settings

router = APIRouter()
ai_engine = RetailAIModel()

@router.post("/admin/upload-leaflet")
async def upload_leaflet(
    file: UploadFile = File(...),
    supplier: str = Form(...),
    type: str = Form(...),
    region: str = Form("National")
):
    """
    Endpoint for Admin Dashboard to upload leaflets for extraction.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    is_retail = (type.lower() == "supermarket")
    
    # 1. Save file locally
    temp_filename = f"temp_{uuid.uuid4().hex}.pdf"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Extract Data via Gemini
        extracted_data = ai_engine.extract_products_from_local_pdf(temp_filename, supplier, is_retail)
        
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
    if not extracted_data:
        raise HTTPException(status_code=500, detail="Failed to extract any data from the PDF.")
        
    # 3. Format and Save to Supabase
    table_name = "retail_inventory" if is_retail else "wholesale_inventory"
    supabase_url = f"{settings.SUPABASE_URL}/rest/v1/{table_name}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    records_to_insert = []
    
    # Allowed columns based on the database schema
    retail_allowed_keys = {"item", "price", "category", "deal_expiry", "loss_leader_flag", "brand", "region", "type", "image_url"}
    wholesale_allowed_keys = {"supplier", "item", "bulk_price", "estimated_markup_potential", "image_url"}

    for item in extracted_data:
        # 1. Start with an empty record to avoid extra AI keys
        record = {}
        
        # 2. Extract and Sanitize Fields
        if is_retail:
            record["item"] = item.get("item", "Unknown Item")
            record["category"] = item.get("category", "Uncategorized")
            record["deal_expiry"] = item.get("deal_expiry", "Unknown")
            record["loss_leader_flag"] = item.get("loss_leader_flag", False)
            record["brand"] = supplier
            record["region"] = region
            record["type"] = "formal_retail"
            record["image_url"] = item.get("image_url")
            
            # Price sanitization
            raw_price = item.get("price")
            try:
                price_str = str(raw_price).replace("R", "").replace(",", "").strip()
                record["price"] = float(price_str)
            except (ValueError, TypeError):
                record["price"] = 0.0
                
            # Filter strictly to retail keys
            record = {k: v for k, v in record.items() if k in retail_allowed_keys}
            
        else:
            record["item"] = item.get("item", "Unknown Item")
            record["supplier"] = supplier
            record["estimated_markup_potential"] = item.get("estimated_markup_potential", "0%")
            record["image_url"] = item.get("image_url")
            
            # Bulk price sanitization
            raw_bulk = item.get("bulk_price", item.get("unit_price"))
            try:
                price_str = str(raw_bulk).replace("R", "").replace(",", "").strip()
                record["bulk_price"] = float(price_str)
            except (ValueError, TypeError):
                record["bulk_price"] = 0.0
                
            # Filter strictly to wholesale keys
            record = {k: v for k, v in record.items() if k in wholesale_allowed_keys}

        records_to_insert.append(record)
        
    # Send to Supabase
    try:
        response = requests.post(supabase_url, headers=headers, json=records_to_insert)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to save to Supabase: {e}")
        if hasattr(e, 'response') and e.response:
            print(e.response.text)
        raise HTTPException(status_code=500, detail=f"Database save failed: {e}")
        
    return {
        "status": "success",
        "message": f"Successfully extracted and saved {len(records_to_insert)} items for {supplier}.",
        "items": len(records_to_insert)
    }
