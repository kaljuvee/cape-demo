"""
Database utility functions for session data storage\nDeveloped by [Julian Kaljuvee](https://kaljuvee.github.io)"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

DB_PATH = "db/cape_data.db"

def init_database():
    """
    Initialize the SQLite database with required tables
    """
    # Create db directory if it doesn't exist
    os.makedirs("db", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create cape_calculations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cape_calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            calculation_type TEXT,
            ticker TEXT,
            date TEXT,
            cape_value REAL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)
    
    # Create search_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            search_query TEXT,
            results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)
    
    # Create cached_data table for storing downloaded data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT,
            ticker TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def create_session(session_id):
    """
    Create a new session in the database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_id)
            VALUES (?)
        """, (session_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating session: {e}")
    finally:
        conn.close()

def update_session_access(session_id):
    """
    Update the last accessed timestamp for a session
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE sessions 
            SET last_accessed = CURRENT_TIMESTAMP
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating session access: {e}")
    finally:
        conn.close()

def save_cape_calculation(session_id, calculation_type, ticker, date, cape_value, metadata=None):
    """
    Save a CAPE calculation result to the database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute("""
            INSERT INTO cape_calculations 
            (session_id, calculation_type, ticker, date, cape_value, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, calculation_type, ticker, date, cape_value, metadata_json))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving CAPE calculation: {e}")
    finally:
        conn.close()

def get_cape_calculations(session_id, calculation_type=None):
    """
    Retrieve CAPE calculations for a session
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        query = """
            SELECT calculation_type, ticker, date, cape_value, metadata, created_at
            FROM cape_calculations
            WHERE session_id = ?
        """
        params = [session_id]
        
        if calculation_type:
            query += " AND calculation_type = ?"
            params.append(calculation_type)
        
        query += " ORDER BY created_at DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except sqlite3.Error as e:
        print(f"Error retrieving CAPE calculations: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def save_search_history(session_id, search_query, results):
    """
    Save search history to the database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        results_json = json.dumps(results)
        cursor.execute("""
            INSERT INTO search_history (session_id, search_query, results)
            VALUES (?, ?, ?)
        """, (session_id, search_query, results_json))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving search history: {e}")
    finally:
        conn.close()

def get_search_history(session_id, limit=10):
    """
    Retrieve search history for a session
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        query = """
            SELECT search_query, results, created_at
            FROM search_history
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[session_id, limit])
        
        # Parse JSON results
        if not df.empty:
            df['results'] = df['results'].apply(lambda x: json.loads(x) if x else [])
        
        return df
    except sqlite3.Error as e:
        print(f"Error retrieving search history: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def cache_data(data_type, ticker, data, expires_hours=24):
    """
    Cache data in the database with expiration
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        data_json = json.dumps(data, default=str)  # Handle datetime objects
        expires_at = datetime.now().timestamp() + (expires_hours * 3600)
        
        # Delete existing cache for this data type and ticker
        cursor.execute("""
            DELETE FROM cached_data 
            WHERE data_type = ? AND ticker = ?
        """, (data_type, ticker))
        
        # Insert new cache
        cursor.execute("""
            INSERT INTO cached_data (data_type, ticker, data_json, expires_at)
            VALUES (?, ?, ?, datetime(?, 'unixepoch'))
        """, (data_type, ticker, data_json, expires_at))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error caching data: {e}")
    finally:
        conn.close()

def get_cached_data(data_type, ticker):
    """
    Retrieve cached data if not expired
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT data_json FROM cached_data
            WHERE data_type = ? AND ticker = ? 
            AND expires_at > CURRENT_TIMESTAMP
        """, (data_type, ticker))
        
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    except sqlite3.Error as e:
        print(f"Error retrieving cached data: {e}")
        return None
    finally:
        conn.close()

def cleanup_expired_cache():
    """
    Remove expired cache entries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM cached_data 
            WHERE expires_at < CURRENT_TIMESTAMP
        """)
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Error cleaning up cache: {e}")
        return 0
    finally:
        conn.close()

def get_session_stats(session_id):
    """
    Get statistics for a session
    """
    conn = sqlite3.connect(DB_PATH)
    
    try:
        stats = {}
        
        # Count calculations
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM cape_calculations WHERE session_id = ?
        """, (session_id,))
        stats['calculations_count'] = cursor.fetchone()[0]
        
        # Count searches
        cursor.execute("""
            SELECT COUNT(*) FROM search_history WHERE session_id = ?
        """, (session_id,))
        stats['searches_count'] = cursor.fetchone()[0]
        
        # Get session info
        cursor.execute("""
            SELECT created_at, last_accessed FROM sessions WHERE session_id = ?
        """, (session_id,))
        session_info = cursor.fetchone()
        if session_info:
            stats['created_at'] = session_info[0]
            stats['last_accessed'] = session_info[1]
        
        return stats
    except sqlite3.Error as e:
        print(f"Error getting session stats: {e}")
        return {}
    finally:
        conn.close()
