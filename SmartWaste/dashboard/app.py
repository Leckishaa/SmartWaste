from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from collections import Counter

# 📌 Absolute DB path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'database', 'waste.db'))
USER_FILE = os.path.join(BASE_DIR, 'current_user.txt')
print("✅ Using DB Path:", DB_PATH)
print("✅ Current user file path:", USER_FILE)
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ✅ Ensure DB and table exist
def create_users_table():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Make sure database folder exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
    ''')
    conn.commit()
    conn.close()

# 📊 Load data for dashboard and leaderboard
def get_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT student_id, student_name, SUM(points) as total_points
        FROM submissions
        GROUP BY student_id, student_name
        ORDER BY total_points DESC
    ''')
    leaderboard = cursor.fetchall()

    cursor.execute('''
        SELECT student_id, student_name, predicted_label, points, date_submitted
        FROM submissions
        ORDER BY date_submitted DESC
    ''')
    history = cursor.fetchall()

    cursor.execute('SELECT predicted_label FROM submissions')
    all_labels = cursor.fetchall()
    counts = Counter(lable[0] for lable in all_labels)

    conn.close()
    return leaderboard, history, counts

# 🔐 Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE student_id = ? AND password = ?", (student_id, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['logged_in'] = True
            session['name'] = user[2]
            session['role'] = user[4]
            session['student_id'] = user[1]

            # Save current user to file
            # Save current user to file (absolute path so main.py can read reliably)
            try:
                with open(USER_FILE, "w", encoding="utf-8") as f:
                    f.write(f"{user[1]},{user[2]},{user[4]}")  # student_id, name, role
            except OSError as e:
                app.logger.error(f"Failed to write {USER_FILE}: {e}")

            print(f"✅ Logged in as {session['name']} with role {session['role']}")

            if user[4] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('leaderboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')



# 📊 Admin dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))
    leaderboard, history, counts = get_data()
    return render_template('index.html', leaderboard=leaderboard, history=history, counts=counts)

# 📈 Leaderboard
@app.route('/leaderboard')
def leaderboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    leaderboard, history, counts = get_data()
    return render_template('leaderboard.html', leaderboard=leaderboard)

# 🔓 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 👥 Manage Users Page
@app.route('/manage_users')
def manage_users():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('manage_users.html', users=users)

# ➕ Add User
@app.route('/add_user', methods=['POST'])
def add_user():
    student_id = request.form['student_id'].strip()
    name = request.form['name'].strip()
    password = request.form['password'].strip()
    role = request.form['role'].strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (student_id, name, password, role) VALUES (?, ?, ?, ?)",
            (student_id, name, password, role)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "❌ Student ID already exists."
    conn.close()
    return redirect(url_for('manage_users'))

# ✏️ Edit User
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        cursor.execute('''
            UPDATE users SET student_id = ?, name = ?, password = ?, role = ? WHERE id = ?
        ''', (student_id, name, password, role, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_users'))

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('edit_user.html', user=user)

# 🗑️ Delete User
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_users'))

# 🔁 Run App
if __name__ == '__main__':
    create_users_table()
    app.run(debug=True)




