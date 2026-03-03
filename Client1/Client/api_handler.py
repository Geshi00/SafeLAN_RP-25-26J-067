import requests
import os
import json
from config.client_settings import SERVER_URL

class SafeLAN_API:
    def __init__(self):
        self.url = SERVER_URL

    def upload_enrollment(self, uid, m_path, s_path, context, password):
        """Vaults model, context, and password. Corrected 5-arg signature."""
        try:
            with open(m_path, 'rb') as m_file, open(s_path, 'rb') as s_file:
                files = {
                    'model': (os.path.basename(m_path), m_file),
                    'scaler': (os.path.basename(s_path), s_file)
                }
                # 'data' maps to Form(...) fields in FastAPI
                data = {
                    'context': str(context), 
                    'password': password 
                }
                r = requests.post(f"{self.url}/vault/upload/{uid}", files=files, data=data)
                return r.status_code == 200
        except Exception as e:
            print(f"API Upload Error: {e}")
            return False

    def download_model(self, uid):
        """Downloads the personalized SVM and Scaler for local analysis."""
        try:
            os.makedirs('Client/storage/temp', exist_ok=True)
            paths = {}
            for f_type in ['model', 'scaler']:
                r = requests.get(f"{self.url}/vault/download/{uid}/{f_type}")
                if r.status_code == 200:
                    ext = "svm.pkl" if f_type == "model" else "scaler.pkl"
                    path = f"Client/storage/temp/{uid}_{ext}"
                    with open(path, 'wb') as f: f.write(r.content)
                    paths[f_type] = path
            return paths.get('model'), paths.get('scaler')
        except Exception as e: return None, None

    def verify_auth(self, uid, password, score, dna, ctx):
        """Sends full MFA payload for server-side Trust Index calculation."""
        payload = {
            "username": uid, "password": password, 
            "svm_score": float(score), "dna_features": dna, "context": ctx
        }
        r = requests.post(f"{self.url}/auth/verify", json=payload)
        return r.json() if r.status_code == 200 else {"status": "ERROR"}