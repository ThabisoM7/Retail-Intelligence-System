import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load env variables directly if running as standalone script
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://ris_user:ris_password@localhost:5432/ris_wholesale")

def init_db():
    print(f"Connecting to database: {DB_URL}")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wholesale_inventory (
            id SERIAL PRIMARY KEY,
            supplier VARCHAR(100) NOT NULL,
            item VARCHAR(255) NOT NULL,
            bulk_price DECIMAL(10, 2) NOT NULL,
            estimated_markup_potential VARCHAR(50)
        );
        """)

        # Insert some mock data
        cursor.execute("TRUNCATE TABLE wholesale_inventory;")
        cursor.execute("""
        INSERT INTO wholesale_inventory (supplier, item, bulk_price, estimated_markup_potential) VALUES
        ('Kit Kat Cash & Carry', 'Cooking Oil 2L (Box of 6)', 420.00, '22%'),
        ('Kit Kat Cash & Carry', 'Maize Meal 10kg (Bale of 5)', 350.00, '18%'),
        ('Redstar Wholesale', 'White Bread (Crate of 10)', 120.00, '30%'),
        ('Big Save', 'Milk 1L (Case of 6)', 130.00, '25%');
        """)

        print("Database initialized successfully.")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    init_db()
