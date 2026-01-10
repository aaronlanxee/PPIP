import sqlite3

# Connect to database (creates file if not exist)
conn = sqlite3.connect("ppip.db")
cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Create pets table
cursor.execute("""
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    breed TEXT,
    image BLOB,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# Commit changes and close
conn.commit()
conn.close()
print("Database and tables created successfully!")
