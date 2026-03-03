import numpy as np
import joblib
import io
import os
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

def train_model_locally(features_list):
    """
    Trains the SVM and Scaler on the client and returns memory buffers.
    """
    try:
        X = np.array(features_list)
        # Add jitter to prevent zero-variance math errors
        X = X + np.random.normal(0, 1e-7, X.shape)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = OneClassSVM(kernel='rbf', gamma=0.01, nu=0.05)
        model.fit(X_scaled)
        
        # Serialize to BytesIO buffers
        model_buf = io.BytesIO()
        joblib.dump(model, model_buf)
        model_buf.seek(0)
        
        scaler_buf = io.BytesIO()
        joblib.dump(scaler, scaler_buf)
        scaler_buf.seek(0)
        
        dna_mean = np.mean(X, axis=0).tolist()
        
        return model_buf, scaler_buf, dna_mean
    except Exception as e:
        print(f"Local Training Failed: {e}")
        return None, None, None