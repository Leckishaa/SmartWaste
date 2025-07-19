import sqlite3

DB_PATH = 'C:/SmartWaste/database/waste.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Insert test student
cursor.execute("INSERT INTO users (student_id, name, password, role) VALUES (?, ?, ?, ?)",
               ('S0001', 'John Doe', 'student123', 'student'))

conn.commit()
conn.close()

print("✅ Student user inserted")
