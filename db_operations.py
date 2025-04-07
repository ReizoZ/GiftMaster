import sqlite3
import json
import logging
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

def init_db():
    """Initialize the SQLite database and create giveaways table if it doesn't exist."""
    conn = sqlite3.connect('./Database/giveaways.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS giveaways (
        message_id TEXT PRIMARY KEY,
        member TEXT,
        title TEXT,
        winner TEXT,
        time INTEGER,
        description TEXT,
        entries INTEGER,
        entrants TEXT,
        winners TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        display_name TEXT,
        discriminator TEXT,
        avatar TEXT,
        created_at TEXT,
        joined_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("SQLite database initialized")

def save_giveaway_to_db(message_id: str, data: dict) -> None:
    """
    Save giveaway data to SQLite database.
    
    Args:
        message_id: The Discord message ID of the giveaway
        data: Dictionary containing giveaway data including:
            - member: Host member mention
            - Title: Giveaway title
            - Winner: Number of winners
            - Time: Duration in seconds
            - Description: Giveaway description
            - Entries: Number of entries
            - Entrants: List of user IDs who entered
            - Winners: List of winner user IDs
    """
    conn = sqlite3.connect('./Database/giveaways.db')
    cursor = conn.cursor()
    
    for user_data in data.get("Entrants", []):
        if isinstance(user_data, dict):  
            cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, display_name, discriminator, avatar, created_at, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get("id"),
                user_data.get("username"),
                user_data.get("display_name"),
                user_data.get("discriminator"),
                user_data.get("avatar"),
                user_data.get("created_at"),
                user_data.get("joined_at")
            ))
    
    entrants_ids = [u.get("id") if isinstance(u, dict) else u for u in data.get("Entrants", [])]
    winners_ids = [u.get("id") if isinstance(u, dict) else u for u in data.get("Winners", [])]
    entrants_json = json.dumps(entrants_ids)
    winners_json = json.dumps(winners_ids)
    
    cursor.execute('''
    INSERT OR REPLACE INTO giveaways 
    (message_id, member, title, winner, time, description, entries, entrants, winners)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        message_id,
        data.get("member", ""),
        data.get("Title", ""),
        data.get("Winner", ""),
        data.get("Time", 0),
        data.get("Description", ""),
        data.get("Entries", 0),
        entrants_json,
        winners_json
    ))
    
    conn.commit()
    conn.close()
    logging.info(f"Saved giveaway {message_id} to database")

def get_giveaway_from_db(message_id: str) -> dict | None:
    """
    Retrieve giveaway data from SQLite database.
    
    Args:
        message_id: The Discord message ID of the giveaway
        
    Returns:
        Dictionary containing giveaway data or None if not found
    """
    conn = sqlite3.connect('./Database/giveaways.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM giveaways WHERE message_id = ?', (message_id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return None
    
    data = dict(row)
    
    entrants_str = data.get("entrants", "[]")
    if isinstance(entrants_str, str):
        try:
            entrants_ids = json.loads(entrants_str)
        except json.JSONDecodeError:
            if '"' in entrants_str:
                entrants_ids = [id.strip('" ') for id in entrants_str.strip('[]').split(',')]
            else:
                entrants_ids = entrants_str.strip('[]').split()
    
    winners_str = data.get("winners", "[]")
    if isinstance(winners_str, str):
        try:
            winners_ids = json.loads(winners_str)
        except json.JSONDecodeError:
            if '"' in winners_str:
                winners_ids = [id.strip('" ') for id in winners_str.strip('[]').split(',')]
            else:
                winners_ids = winners_str.strip('[]').split()

    
    data["Entrants"] = []
    data["Winners"] = []
    cursor.execute('SELECT * FROM users WHERE user_id = ?', ((data.get("member", "")[2:-1]),))
    data["hoster"] = cursor.fetchone()

    
    for user_id in entrants_ids:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            data["Entrants"].append(dict(user_row))
        else:
            data["Entrants"].append(user_id)  
    
    for user_id in winners_ids:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (int(user_id[2:-1]),))
        user_row = cursor.fetchone()
        if user_row:
            data["Winners"].append(dict(user_row))
        else:
            data["Winners"].append(user_id) 
    result = {
        "member": data.get("member", ""),
        "Title": data.get("title", ""),
        "Winner": data.get("winner", ""),
        "Time": data.get("time", 0),
        "Description": data.get("description", ""),
        "Entries": data.get("entries", 0),
        "Entrants": data.get("Entrants", []),
        "Winners": data.get("Winners", []),
        "Hoster": data.get("hoster", [])

    }
    conn.close()
    return result

def get_all_giveaways_from_db() -> dict:
    """
    Retrieve all giveaways from SQLite database.
    
    Returns:
        Dictionary where keys are message IDs and values are giveaway data dictionaries
    """
    conn = sqlite3.connect('./Database/giveaways.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM giveaways')
    rows = cursor.fetchall()
    
    result = {}
    for row in rows:
        data = dict(row)
        message_id = data["message_id"]
        
        data["Entrants"] = json.loads(data.get("entrants", "[]"))
        data["Winners"] = json.loads(data.get("winners", "[]"))
        
        result[message_id] = {
            "member": data.get("member", ""),
            "Title": data.get("title", ""),
            "Winner": data.get("winner", ""),
            "Time": data.get("time", 0),
            "Description": data.get("description", ""),
            "Entries": data.get("entries", 0),
            "Entrants": data.get("Entrants", []),
            "Winners": data.get("Winners", [])
        }
    
    conn.close()
    return result
