# config/server_settings.py

# Decision Thresholds
TI_SUCCESS = 85.0
TI_CHALLENGE = 60.0

# Context Point System (Sc)
POINTS_UUID, POINTS_MAC, POINTS_SUBNET, POINTS_HOSTNAME, POINTS_REGISTRY = 50, 20, 10, 10, 10

# Storage Paths (ADD THESE IF MISSING)
DB_PATH = "server/safelan_vault.db"
AUDIT_LOG_CSV = "server/logs/forensic_audit.csv"
MODEL_VAULT = "server/storage/user_models/"
RAW_VAULT = "server/storage/raw_keystrokes/"