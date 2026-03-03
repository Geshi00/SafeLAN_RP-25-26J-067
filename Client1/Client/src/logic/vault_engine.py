import requests
import os
from Client.src.logic.config_mgr import load_server_config

class VaultEngine:
    def __init__(self):
        # Initial load from file
        config = load_server_config()
        self.api_base = f"http://{config['ip']}:{config['port']}"

    def get_vault_data(self, current_user):
        """Fetches files filtered by user identity."""
        try:
            params = {"user": current_user}
            # The URL is constructed dynamically from self.api_base
            r = requests.get(f"{self.api_base}/files/list", params=params, timeout=3)
            if r.status_code == 200:
                files = r.json()
                total_size = sum([float(f.get('size', '0').split()[0]) for f in files])
                return {"files": files, "count": len(files), "total_kb": total_size}
            return {"files": [], "count": 0, "total_kb": 0}
        except Exception as e:
            print(f"Network Connection Failed: {self.api_base}")
            return {"files": [], "count": 0, "total_kb": 0}

    def upload_file(self, local_path, owner_name, target="PUBLIC"):
        try:
            with open(local_path, "rb") as f:
                r = requests.post(f"{self.api_base}/files/upload", 
                                files={"file": (os.path.basename(local_path), f)}, 
                                data={"owner": owner_name, "target": target}, timeout=5)
                return r.status_code == 200
        except: return False

    def download_file(self, filename, save_path):
        try:
            r = requests.get(f"{self.api_base}/files/download/{filename}", stream=True, timeout=10)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                return True
            return False
        except: return False

    def delete_file(self, filename):
        try: return requests.delete(f"{self.api_base}/files/delete/{filename}", timeout=3).status_code == 200
        except: return False