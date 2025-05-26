import sqlite3

# Decide DB name
db_name = 'headlines.db'


conn = sqlite3.connect(db_name)
c = conn.cursor()

# Create the table for Reuters headlines
c.execute("""
    CREATE TABLE IF NOT EXISTS reuters_headlines (
        timestamp TEXT, 
        news TEXT
    )
""")

# Create the table for CNBC headlines
c.execute("""
    CREATE TABLE IF NOT EXISTS CNBC_headlines (
        timestamp TEXT, 
        news TEXT
    )
""")

# Create the table for Blog Posts
c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()

print("Database tables initialized successfully.")