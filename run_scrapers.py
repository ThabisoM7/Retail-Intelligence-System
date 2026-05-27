from app.scrapers.redstar import RedStarScraper
from app.scrapers.bigsave import BigSaveScraper
from app.scrapers.kitkat import KitKatScraper
from app.scrapers.devland import DevlandScraper
from supabase import create_client, Client
from app.core.config import settings

def reset_table():
    print("Clearing old wholesale inventory data...")
    try:
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Delete all records by matching all IDs greater than 0
            # Note: In production you might want to soft delete or upsert, but for MVP this is fine
            response = supabase.table("wholesale_inventory").delete().gt("id", 0).execute()
            print(f"Table cleared successfully. Deleted {len(response.data)} old rows.")
        else:
            print("Skipped clearing: Missing Supabase credentials.")
            
    except Exception as e:
        print(f"Error clearing table via Supabase REST: {e}")

def main():
    print("=== RIS Wholesale Data Ingestion Engine ===")
    
    # 1. Clear old data to prevent duplicates
    reset_table()
    
    # 2. Initialize Scrapers
    scrapers = [
        RedStarScraper(),
        BigSaveScraper(),
        KitKatScraper(),
        DevlandScraper()
    ]
    
    # 3. Execute and Save
    for scraper in scrapers:
        print("\n-----------------------------------")
        scraper.scrape()
        scraper.save_to_db()
        
    print("\n=== Ingestion Complete ===")

if __name__ == "__main__":
    main()
