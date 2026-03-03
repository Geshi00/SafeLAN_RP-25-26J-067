import requests
from Client.src.logic.dna_engine import extract_dna_features
from Client.src.utils.context import get_contextual_data
from Client.src.logic.config_mgr import load_server_config

class AuthEngine:
    def __init__(self):
        config = load_server_config()
        self.api_base = f"http://{config['ip']}:{config['port']}"

    def update_endpoint(self, new_url):
        self.api_base = new_url
        print(f"[*] AuthEngine logic synced to: {self.api_base}")

    def extract_dna_features(self, events):
        return extract_dna_features(events)

    def verify(self, username, events, password):
        dna = self.extract_dna_features(events)
        if not dna:
            return {"status": "DENIED_INSUFFICIENT_DATA", "trust_index": 0, "svm_score": 0.0}

        ctx_data = get_contextual_data()
        server_ctx = {
            "machine_id": ctx_data.get('machine_id'),
            "mac": ctx_data.get('mac'),
            "ip": ctx_data.get('ip'),
            "hostname": ctx_data.get('hostname'),
            "reg_key": "SECURE_GATEWAY_V1"
        }

        payload = {
            "username": username,
            "password": password,
            "dna_features": dna,
            "context": server_ctx
        }

        try:
            # INCREASED TIMEOUT: 25 seconds to prevent "Read timed out"
            r = requests.post(f"{self.api_base}/auth/verify", json=payload, timeout=25)
            
            if r.status_code == 200:
                data = r.json()
                print(f"[DEBUG] Auth successful via {self.api_base}")
                return data
            
            return {"status": "SERVER_ERROR", "trust_index": 0, "svm_score": 0.0}
            
        except requests.exceptions.Timeout:
            print(f"[!] Server Timeout: Machine under heavy load.")
            return {"status": "OFFLINE", "trust_index": 0, "svm_score": 0.0, "message": "Server timeout"}
        except Exception as e:
            print(f"[!] Network Error on {self.api_base}: {e}")
            return {"status": "OFFLINE", "trust_index": 0, "svm_score": 0.0}