import base64
import os
from dotenv import load_dotenv
from backend.database import get_db_connection
from langchain_community.chat_message_histories import ChatMessageHistory, SQLChatMessageHistory

load_dotenv()

DB_PATH = os.getenv("CHAT_DATABASE_URL")

def decode_file(base64_encoded_str):
    """Decodes a base64 encoded string to raw string correctly."""
    return base64.b64decode(base64_encoded_str.encode())

def get_message_history(session_id: str) -> ChatMessageHistory:
    """Get chat history for a session_id"""
    return SQLChatMessageHistory(session_id, DB_PATH)

# Resume database storage

def store_resume(user_id: str, resume_text: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resumes (user_id, resume_raw)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET resume_raw=excluded.resume_raw;
    """, (user_id, resume_text))
    conn.commit()
    conn.close()

def get_resume(user_id: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT resume_raw FROM resumes WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def store_parsed_resume(user_id: str, parsed_json_str: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resumes SET resume_parsed = ?
        WHERE user_id = ?;
    """, (parsed_json_str, user_id))
    conn.commit()
    conn.close()

def get_parsed_resume(user_id: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT resume_parsed FROM resumes WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None