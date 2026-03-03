import uvicorn
import os
import sys
from server.database import init_db
from config.server_settings import MODEL_VAULT, RAW_VAULT

def pre_flight_check():
    """Ensures the server environment is prepared before accepting connections."""
    print("🛡️  SafeLAN-Auth: Performing Pre-Flight Checks...")
    
    # 1. Create necessary directories for the Vault and Logs
    required_dirs = [
        "server/storage",
        MODEL_VAULT,
        RAW_VAULT,
        "server/logs"
    ]
    
    for folder in required_dirs:
        if not os.path.exists(folder):
            print(f"[+] Creating missing directory: {folder}")
            os.makedirs(folder, exist_ok=True)

    # 2. Initialize SQLite Metadata Database
    try:
        if not os.path.exists("server/safelan_vault.db"):
            print("[+] Database not found. Initializing safelan_vault.db...")
            init_db()
        else:
            print("[ok] Database found.")
    except Exception as e:
        print(f"[!] Critical Error during DB init: {e}")
        sys.exit(1)

    print("[ok] Environment Ready.\n")

if __name__ == "__main__":
    # Perform setup
    pre_flight_check()
    
    # Launch FastAPI Server
    # host="0.0.0.0" allows other PCs on your LAN to connect to this server
    print("🚀 SafeLAN-Auth Decision Engine starting on port 8000...")
    uvicorn.run(
        "server.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True  # Useful for development; auto-restarts on code changes
    )