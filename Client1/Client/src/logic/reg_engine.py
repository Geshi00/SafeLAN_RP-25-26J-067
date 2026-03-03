import requests, json, os
from Client.src.logic.dna_engine import extract_dna_features
from Client.src.features.trainer import train_model_locally
from Client.src.utils.context import get_contextual_data
from Client.src.logic.config_mgr import load_server_config

class RegEngine:
    def __init__(self):
        self.samples_events = []
        config = load_server_config()
        self.api_base = f"http://{config['ip']}:{config['port']}"

    def add_sample(self, events):
        if events: 
            self.samples_events.append(list(events))
        return len(self.samples_events)

    def ready(self):
        try:
            from config.client_settings import REQUIRED_SAMPLES
        except ImportError:
            REQUIRED_SAMPLES = 5
        return len(self.samples_events) >= REQUIRED_SAMPLES

    def save_and_train(self, username, password, email):
        """Extracts features, trains locally, and uploads to server with Email context."""
        
        # 1. Feature Extraction
        all_features = [extract_dna_features(e) for e in self.samples_events if extract_dna_features(e)]
        
        if len(all_features) < 3:
            return False

        # 2. Local Training
        model_bytes, scaler_bytes, dna_mean = train_model_locally(all_features)
        if not model_bytes: return False

        # 3. Contextual Data
        ctx = get_contextual_data()
        ctx['reg_key'] = "SECURE_GATEWAY_V1"

        # 4. Payload Preparation (NOW INCLUDING EMAIL)
        payload = {
            "username": username,
            "password": password,
            "email": email, # <--- NEW FIELD
            "dna_means": json.dumps(dna_mean),
            "context": json.dumps(ctx)
        }
        
        files = {
            "model": ("svm.pkl", model_bytes, "application/octet-stream"),
            "scaler": ("scaler.pkl", scaler_bytes, "application/octet-stream")
        }

        try:
            r = requests.post(f"{self.api_base}/auth/register", data=payload, files=files, timeout=25)
            return r.status_code == 200 and r.json().get("status") == "SUCCESS"
        except Exception as e:
            print(f"[!] Registration Upload Failed: {e}")
            return False