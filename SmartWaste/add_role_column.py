import sqlite3

# Fix the path to point to the correct location
conn = sqlite3.connect('database/waste.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
    print("✅ 'role' column added successfully.")
except sqlite3.OperationalError as e:
    print("⚠️ Error (maybe column already exists):", e)

conn.commit()
conn.close()

