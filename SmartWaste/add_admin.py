import sqlite3

DB_PATH = 'C:/SmartWaste/database/waste.db'  # Make sure this path is correct

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Insert admin user
cursor.execute("INSERT INTO users (student_id, name, password, role) VALUES (?, ?, ?, ?)",
               ('admin', 'Admin', 'admin123', 'admin'))

conn.commit()
conn.close()

print("✅ Admin user inserted")
