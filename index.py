from flask import Flask, request, jsonify
import sqlite3
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Helper function to connect to SQLite
def get_db_connection():
    conn = sqlite3.connect('poem_website.db')
    conn.row_factory = sqlite3.Row  # So we can get results as dictionaries
    return conn

# Function to create tables if they don't exist
def create_tables():
    conn = get_db_connection()

    # Create users table
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')

    # Create poems table
    conn.execute('''CREATE TABLE IF NOT EXISTS poems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER
    )''')

    # Add poet column if it doesn't exist
    try:
        conn.execute("ALTER TABLE poems ADD COLUMN poet TEXT;")
    except sqlite3.OperationalError:
        # This error is raised if the column already exists
        pass

    conn.commit()
    conn.close()

# Call the function to create tables on application startup
create_tables()

# User Registration Endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

# User Login Endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': 'Login successful', 'user_id': user['id']}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Submit a Poem Endpoint
@app.route('/api/poems', methods=['POST'])
def submit_poem():
    data = request.json
    title = data['title']
    content = data['content']
    user_id = data['user_id']
    poet = data['poet']

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO poems (title, content, user_id, poet) VALUES (?, ?, ?, ?)",
        (title, content, user_id, poet)
    )
    conn.commit()
    conn.close()

    return jsonify({'message': 'Poem submitted successfully!'}), 201

# Get Poems Endpoint
@app.route('/api/poems', methods=['GET'])
def get_poems():
    conn = get_db_connection()
    poems = conn.execute('SELECT * FROM poems').fetchall()
    conn.close()

    poem_list = []
    for poem in poems:
        poem_list.append({
            'id': poem['id'],
            'title': poem['title'],
            'content': poem['content'],
            'user_id': poem['user_id'],
            'poet': poem['poet'],
        })

    return jsonify(poem_list), 200

# Delete a Poem Endpoint
@app.route('/api/poems/<int:id>', methods=['DELETE'])
def delete_poem(id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM poems WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'message': 'Poem deleted successfully!'}), 204  # No Content
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
