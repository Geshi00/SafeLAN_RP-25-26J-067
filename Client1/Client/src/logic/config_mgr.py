import json
import os

CONFIG_FILE = "client_config.json"

def save_server_config(ip, port):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"ip": ip, "port": port}, f)

def load_server_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"ip": "127.0.0.1", "port": "8000"} # Default