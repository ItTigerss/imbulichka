import sqlite3
import os
import json

class Database:
    def __init__(self):
        self.db_path = "data/database.db"
        self.init_db()
    
    def init_db(self):
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                messages INTEGER DEFAULT 0,
                voice_time INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 1000,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # Cards collection
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_id TEXT,
                card_name TEXT,
                rarity TEXT,
                obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int, guild_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'guild_id': row[1],
                'xp': row[2],
                'level': row[3],
                'messages': row[4],
                'voice_time': row[5],
                'coins': row[6]
            }
        return None
    
    def create_user(self, user_id: int, guild_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, guild_id, coins) VALUES (?, ?, 1000)",
            (user_id, guild_id)
        )
        conn.commit()
        conn.close()
    
    def update_xp(self, user_id: int, guild_id: int, xp: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET xp = xp + ? WHERE user_id = ? AND guild_id = ?",
            (xp, user_id, guild_id)
        )
        conn.commit()
        conn.close()
    
    def update_level(self, user_id: int, guild_id: int, level: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET level = ? WHERE user_id = ? AND guild_id = ?",
            (level, user_id, guild_id)
        )
        conn.commit()
        conn.close()
    
    def update_messages(self, user_id: int, guild_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET messages = messages + 1 WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        conn.commit()
        conn.close()
    
    def update_voice_time(self, user_id: int, guild_id: int, minutes: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET voice_time = voice_time + ? WHERE user_id = ? AND guild_id = ?",
            (minutes, user_id, guild_id)
        )
        conn.commit()
        conn.close()
    
    def get_top_users(self, guild_id: int, limit: int = 10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_id, xp, level FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

db = Database()