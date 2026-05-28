import requests
import google.generativeai as genai
import os
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
pdf_url = "https://files.sitebuilder.1-grid.com/ba/dd/baddd098-49d8-4c3c-a6c7-37fd19cecb52.pdf"

print("Downloading PDF...")
r = requests.get(pdf_url)
with open("temp.pdf", "wb") as f:
    f.write(r.content)

print("Uploading to Gemini...")
sample_file = genai.upload_file(path="temp.pdf", display_name="Devland Specials")

print("Extracting...")
model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})
prompt = "Extract products and prices from this catalog. Return a JSON array of objects with keys: 'item' and 'bulk_price'."
response = model.generate_content([prompt, sample_file])
print(response.text[:500])

genai.delete_file(sample_file.name)
os.remove("temp.pdf")
print("Done.")
