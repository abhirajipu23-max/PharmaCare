import psycopg2
import os

# Connection Details
# We try both Pooler (port 6543) and Direct (port 5432) if possible (but direct DNS failed earlier)

DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.ysdduqbnbefrwhvkgafo"
DB_PASS = "Uttamkr5898"
DB_PORT = "6543"

print(f"Connecting to {DB_HOST}:{DB_PORT} as {DB_USER}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode='require'
    )
    print("SUCCESS: Connection established!")
    conn.close()
except Exception as e:
    print(f"FAILED: {e}")
