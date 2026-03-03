import requests, os

class FileEngine:
    def __init__(self):
        self.api_base = "http://127.0.0.1:8000"

    def fetch_files(self):
        try:
            return requests.get(f"{self.api_base}/files/list").json()
        except: return []

    def upload(self, path, user):
        with open(path, "rb") as f:
            requests.post(f"{self.api_base}/files/upload", 
                          files={"file": (os.path.basename(path), f)}, data={"owner": user})

    def delete(self, name):
        return requests.delete(f"{self.api_base}/files/delete/{name}").status_code == 200