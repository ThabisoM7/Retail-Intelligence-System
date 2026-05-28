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
    for item in extracted_data:
        record = item.copy()
        if is_retail:
            record["brand"] = supplier
            record["region"] = region
            record["type"] = "formal_retail"
            # Ensure fields map correctly to the new Retail schema
            record["deal_expiry"] = record.get("deal_expiry", "Unknown")
            record["loss_leader_flag"] = record.get("loss_leader_flag", False)
        else:
            record["supplier"] = supplier
            record["unit_price"] = record.get("unit_price", record.get("bulk_price"))
            record["bulk_quantity_savings"] = record.get("bulk_quantity_savings", "")
            
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
