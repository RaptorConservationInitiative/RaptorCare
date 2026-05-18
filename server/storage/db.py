import psycopg2
import os

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://raptorcare:password@localhost:5432/raptorcare"
)

def get_conn():
    return psycopg2.connect(DB_URL)