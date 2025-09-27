import duckdb
import os

DB_PATH = os.getenv("DUCKDB_PATH", "../data/prod.duckdb")

def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)