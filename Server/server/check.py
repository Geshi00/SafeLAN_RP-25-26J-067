import sqlite3
import os

# Ensuring we point to the correct database file
DB_PATH = 'server/safelan_vault.db' 

def audit_database():
    if not os.path.exists(DB_PATH):
        # Fallback to current directory if not in server/
        if os.path.exists('safelan_vault.db'):
            path = 'safelan_vault.db'
        else:
            print(f"[!] Error: Database not found at {os.path.abspath(DB_PATH)}")
            return
    else:
        path = DB_PATH

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- 🏛️ SafeLAN-Auth Vault & Network Audit ---")

    # 1. Audit Biometric Users
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"\n[Users Table] Count: {len(users)}")
        for row in users:
            dna_status = "✅ Populated" if row['dna_means'] else "❌ Empty"
            print(f" - ID {row['id']}: {row['username']} | DNA Baseline: {dna_status}")

        # 2. Audit Device Context (Security Anchors)
        cursor.execute("""
            SELECT u.username, d.hw_uuid, d.mac_address, d.hostname, d.registered_subnet 
            FROM devices d 
            JOIN users u ON d.user_id = u.id
        """)
        devices = cursor.fetchall()
        print(f"\n[Devices Table] Security Anchors: {len(devices)}")
        for row in devices:
            print(f" - User: {row['username']}")
            print(f"   └─ UUID:   {row['hw_uuid']}")
            print(f"   └─ MAC:    {row['mac_address']}")
            print(f"   └─ Subnet: {row['registered_subnet']}")

        # 3. NEW: Audit Network Vault (Permissions & Scopes)
        cursor.execute("SELECT * FROM shared_files")
        files = cursor.fetchall()
        print(f"\n[Network Vault] Shared Resources: {len(files)}")
        
        # Display table-like header for files
        print(f"{'Filename':<25} | {'Owner':<12} | {'Scope/Target':<12} | {'Size'}")
        print("-" * 70)
        
        for f in files:
            # Check for the new target_user column
            target = f['target_user'] if 'target_user' in f.keys() else "LEGACY (No Target)"
            scope_icon = "🌐" if target == "PUBLIC" else "🔐"
            
            print(f"{f['filename'][:25]:<25} | {f['owner']:<12} | {scope_icon} {target:<10} | {f['file_size']}")

    except sqlite3.OperationalError as e:
        print(f"\n[!] Schema Conflict: {e}")
        print("[*] Hint: If 'target_user' is missing, the server migration hasn't run or the DB needs a reset.")
    finally:
        conn.close()

if __name__ == "__main__":
    audit_database()