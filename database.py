import sqlite3

# Initialize database
def create_database():
    conn = sqlite3.connect("appdata.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        user INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(30) UNIQUE NOT NULL,
        password VARCHAR(150) NOT NULL,
        email VARCHAR(50) UNIQUE NOT NULL,
        logged_in INTEGER DEFAULT 0,
        profile_picture BLOB
    )""")
    conn.commit()
    conn.close()

