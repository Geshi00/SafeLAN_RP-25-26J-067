import requests
import json
from Client.src.logic.dna_engine import extract_dna_features
from Client.src.features.trainer import train_model_locally
from Client.src.utils.context import get_contextual_data
from Client.src.logic.config_mgr import load_server_config

class ClientController:
    def __init__(self):
        config = load_server_config()
        self.api_base = f"http://{config['ip']}:{config['port']}"

    def register(self, username, password, samples):
        # 1. Extract and Train Locally
        features = [extract_dna_features(s) for s in samples if extract_dna_features(s)]
        model_buf, scaler_buf, dna_mean = train_model_locally(features)
        
        if not model_buf: return False

        # 2. Prepare API Upload
        ctx = get_contextual_data()
        payload = {
            "username": username,
            "password": password,
            "dna_means": json.dumps(dna_mean),
            "context": json.dumps(ctx)
        }
        
        files = {
            "model": ("svm.pkl", model_buf, "application/octet-stream"),
            "scaler": ("scaler.pkl", scaler_buf, "application/octet-stream")
        }

        # 3. Transmit via API
        try:
            r = requests.post(f"{self.api_base}/auth/register", data=payload, files=files)
            return r.status_code == 200
        except:
            return False