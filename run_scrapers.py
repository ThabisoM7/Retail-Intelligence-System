from app.scrapers.redstar import RedStarScraper
from app.scrapers.bigsave import BigSaveScraper
from app.scrapers.kitkat import KitKatScraper
from app.scrapers.devland import DevlandScraper
from app.scrapers.retail_pdf import ShopriteScraper, SparScraper
import requests
from app.core.config import settings

def reset_table(table_name="wholesale_inventory"):
    print(f"Clearing old {table_name} data...")
    try:
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            url = f"{settings.SUPABASE_URL}/rest/v1/{table_name}"
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}"
            }
            # Delete all records by matching all IDs greater than 0
            response = requests.delete(f"{url}?id=gt.0", headers=headers)
            if response.status_code in (200, 204):
                print(f"Table {table_name} cleared successfully.")
            else:
                print(f"Failed to clear {table_name}. Status: {response.status_code}, Error: {response.text}")
        else:
            print("Skipped clearing: Missing Supabase credentials.")
            
    except Exception as e:
        print(f"Error clearing {table_name} via Supabase REST: {e}")

def main():
    print("=== RIS Data Ingestion Engine ===")
    
    # 1. Clear old data to prevent duplicates
    reset_table("wholesale_inventory")
    reset_table("retail_inventory")
    
    # 2. Initialize Scrapers
    scrapers = [
        RedStarScraper(),
        BigSaveScraper(),
        KitKatScraper(),
        DevlandScraper(),
        ShopriteScraper(),
        SparScraper()
    ]
    
    # 3. Execute and Save
    for scraper in scrapers:
        print("\n-----------------------------------")
        scraper.scrape()
        scraper.save_to_db()
        
    print("\n=== Ingestion Complete ===")

if __name__ == "__main__":
    main()
