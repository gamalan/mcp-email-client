import duckdb
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Define database file path
DB_FILE = Path("emails.duckdb")

def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    with duckdb.connect(str(DB_FILE)) as conn:
        # Create emails table with IDENTITY for auto-incrementing ID
        conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS email_id_seq START 1;
        """)
        
        # Create emails table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                config_name VARCHAR,
                subject VARCHAR,
                body TEXT,
                sender VARCHAR,
                recipients VARCHAR,
                cc VARCHAR,
                bcc VARCHAR,
                date TIMESTAMP,
                raw_content TEXT,
                embedding BLOB  -- For storing vector embeddings later
            )
        """)

def insert_email(
    config_name: str, 
    subject: str, 
    body: str, 
    sender: str = None, 
    recipients: str = None,
    cc: str = None,
    bcc: str = None,
    date: datetime.datetime = None,
    raw_content: str = None
) -> int:
    """Insert an email into the database."""
    if date is None:
        date = datetime.datetime.now()
        
    with duckdb.connect(str(DB_FILE)) as conn:
        try:
            # Get the next ID from sequence
            result = conn.execute("SELECT nextval('email_id_seq')").fetchone()
            next_id = result[0] if result else 1
            
            # Insert the email with explicit ID
            conn.execute("""
                INSERT INTO emails (id, config_name, subject, body, sender, recipients, cc, bcc, date, raw_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (next_id, config_name, subject, body, sender, recipients, cc, bcc, date, raw_content))
            
            return next_id
        except Exception as e:
            # Handle the error more gracefully
            print(f"Error inserting email: {e}")
            # If the error is about the sequence not existing, create it and try again
            if "does not exist" in str(e):
                conn.execute("CREATE SEQUENCE IF NOT EXISTS email_id_seq START 1")
                return insert_email(config_name, subject, body, sender, recipients, cc, bcc, date, raw_content)
            raise

def get_emails(
    config_name: Optional[str] = None,
    limit: int = 10, 
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get emails from database with optional filtering by config_name."""
    with duckdb.connect(str(DB_FILE)) as conn:
        query = "SELECT * FROM emails"
        params = []
        
        if config_name:
            query += " WHERE config_name = ?"
            params.append(config_name)
            
        query += " ORDER BY date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return [dict(zip(columns, row)) for row in result]

def get_emails_by_date_range(
    start_date: datetime.datetime,
    end_date: datetime.datetime = None,
    config_name: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get emails within a specified date range."""
    if end_date is None:
        end_date = datetime.datetime.now()
        
    with duckdb.connect(str(DB_FILE)) as conn:
        query = "SELECT * FROM emails WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if config_name:
            query += " AND config_name = ?"
            params.append(config_name)
            
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return [dict(zip(columns, row)) for row in result]

def get_all_emails(
    config_name: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """Get all emails from the database with optional config_name filtering."""
    with duckdb.connect(str(DB_FILE)) as conn:
        query = "SELECT * FROM emails"
        params = []
        
        if config_name:
            query += " WHERE config_name = ?"
            params.append(config_name)
            
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return [dict(zip(columns, row)) for row in result]

def search_emails_by_content(
    query: str,
    config_name: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Basic text search in email subject and body.
    This will be enhanced with vector search later.
    """
    with duckdb.connect(str(DB_FILE)) as conn:
        sql_query = """
            SELECT * FROM emails 
            WHERE (subject ILIKE ? OR body ILIKE ?)
        """
        params = [f'%{query}%', f'%{query}%']
        
        if config_name:
            sql_query += " AND config_name = ?"
            params.append(config_name)
            
        sql_query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        result = conn.execute(sql_query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        
        return [dict(zip(columns, row)) for row in result]

def get_email_count(config_name: Optional[str] = None) -> int:
    """Get the total count of emails in the database."""
    with duckdb.connect(str(DB_FILE)) as conn:
        query = "SELECT COUNT(*) FROM emails"
        params = []
        
        if config_name:
            query += " WHERE config_name = ?"
            params.append(config_name)
            
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0

# Initialize the database when the module is imported
init_db()