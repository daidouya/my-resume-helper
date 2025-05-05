import sqlite3
import os

DB_PATH = "resume_data.db"

# Ensure table exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        user_id TEXT PRIMARY KEY,
        resume_raw TEXT,
        resume_parsed TEXT
    );
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)