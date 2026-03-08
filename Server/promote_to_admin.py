import sys
import os

# Add the SafeLAN Server directory to the path 
sys.path.append(os.getcwd())

from server.blockchain import Blockchain, Authority

def promote_user(username):
    username = username.upper()
    print(f"Assigning ADMIN role to: {username}...")
    
    # Initialize authority and blockchain
    # Standardize path back to Server directory as per server/blockchain/blockchain.py
    admin_auth = Authority("ADMIN_01", "SafeLAN Central Authority")
    bc = Blockchain(authorities={admin_auth.authority_id: admin_auth.to_dict()})
    
    try:
        bc.register_user(username, "admin")
        bc.save_to_disk()
        print(f"✅ SUCCESS: {username} is now registered as an ADMIN in the blockchain.")
        print(f"Note: restart the server for changes to take effect if it's currently running.")
    except Exception as e:
        print(f"❌ FAILURE: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("SafeLAN Role Management Utility")
        print("-" * 30)
        print("Usage: python promote_to_admin.py <username>")
    else:
        promote_user(sys.argv[1])
