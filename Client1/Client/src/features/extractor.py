import json, os, pandas as pd, joblib, numpy as np
from sklearn.preprocessing import StandardScaler
from src.logic.auth_engine import AuthEngine # Reuse the logic from AuthEngine

def extract_features(user_id):
    raw_path = f'data/raw/{user_id}_raw.json'
    engine = AuthEngine() # Use the extraction logic from the engine
    
    with open(raw_path, 'r') as f:
        data = json.load(f)

    profiles = []
    for sample in data['samples']:
        dna = engine.extract_dna_features(sample)
        if dna: profiles.append(dna)

    df = pd.DataFrame(profiles)
    df.columns = [str(i) for i in range(14)]
    
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)
    
    os.makedirs('models/scalers', exist_ok=True)
    joblib.dump(scaler, f'models/scalers/{user_id}_scaler.pkl')
    # Save the processed features for the SVM trainer
    os.makedirs('data/processed', exist_ok=True)
    pd.DataFrame(scaled, columns=df.columns).to_csv(f'data/processed/{user_id}_features.csv', index=False)