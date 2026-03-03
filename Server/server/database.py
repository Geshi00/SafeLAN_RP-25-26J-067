import sqlite3, os, json, hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), 'safelan_vault.db')

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    # Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        email TEXT,
        dna_means TEXT
    )''')
    # Devices Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        hw_uuid TEXT, mac_address TEXT, registered_subnet TEXT, hostname TEXT, reg_key TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    # Shared Files Table (REQUIRED FOR sync_file_metadata)
    cursor.execute('''CREATE TABLE IF NOT EXISTS shared_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        owner TEXT,
        target_user TEXT DEFAULT 'PUBLIC',
        file_size TEXT,
        upload_date TEXT
    )''')
    conn.commit()
    conn.close()

def save_enrollment(username, password, email, dna_means, ctx):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO users (username, password_hash, email, dna_means) VALUES (?, ?, ?, ?)', 
                           (username, pw_hash, email, json.dumps(dna_means)))
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('''INSERT OR REPLACE INTO devices (user_id, hw_uuid, mac_address, registered_subnet, hostname, reg_key) 
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (user_id, ctx['hw_uuid'], ctx['mac_address'], ctx['registered_subnet'], ctx['hostname'], ctx['reg_key']))
    finally:
        conn.close()

def retrieve_user_identity(username):
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user: return None
    
    cursor.execute('SELECT * FROM devices WHERE user_id = ?', (user['id'],))
    device = cursor.fetchone()
    conn.close()
    
    return {
        "password_hash": user['password_hash'],
        "email": user['email'],
        "dna_means": json.loads(user['dna_means']),
        "device_context": dict(device) if device else None
    }

# --- NEW/RESTORED FILE VAULT FUNCTIONS ---

def sync_file_metadata(filename, owner, target, size, date):
    """Syncs file upload details to the database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    with conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO shared_files 
                          (filename, owner, target_user, file_size, upload_date) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (filename, owner, target, size, date))
    conn.close()

def get_visible_files(current_user):
    """Retrieves list of files visible to the specific user."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM shared_files 
                      WHERE target_user = 'PUBLIC' 
                      OR target_user = ? 
                      OR owner = ?''', (current_user, current_user))
    rows = cursor.fetchall()
    conn.close()
    return [{"name": r["filename"], "owner": r["owner"], "target": r["target_user"], "size": r["file_size"], "date": r["upload_date"]} for r in rows]

def remove_file_metadata(filename):
    """Deletes file metadata upon removal from vault."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    with conn:
        conn.execute('DELETE FROM shared_files WHERE filename = ?', (filename,))
    conn.close()