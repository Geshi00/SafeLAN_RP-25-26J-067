import csv
import os
import hashlib
import numpy as np
from datetime import datetime
from config.server_settings import AUDIT_LOG_CSV
from server.services.otp_service import EmailOTPService

# Initialize the OTP Service for Step-Up Auth
otp_manager = EmailOTPService()

def calculate_trust_index(username, typed_pw, stored_pw_hash, email, svm_score, live_dna, trained_dna_mean, live_ctx, saved_ctx):
    """
    Dynamic Trust-Based Decision Logic:
    1. Knowledge Factor: Binary Password Gate (SHA-256).
    2. Context Score (Sc): Hardware/MAC consistency check (Weight 0.4).
    3. Adaptive Biometric Score (Sb): Linear normalization of SVM distance (Weight 0.6).
    4. Decision Gates:
       - SUCCESS: TI >= 85
       - DENIED: TI < 55
       - CHALLENGE: Intermediate ranges.
    """
    
    # 1. Password Verification (Absolute Hard Gate)
    typed_pw_hash = hashlib.sha256(typed_pw.encode()).hexdigest()
    if typed_pw_hash != stored_pw_hash:
        status = "DENIED (PW_INCORRECT)"
        _log_to_forensics(username, status, 0.0, 0, 0, svm_score, live_dna, trained_dna_mean, live_ctx)
        return {"status": status, "trust_index": 0.0}

    # 2. Dynamic Sc: Context Score (Hardware Match)
    # Machine ID (50 pts) + MAC Address (50 pts)
    sc = sum([
        50 if live_ctx.get('machine_id') == saved_ctx.get('hw_uuid') else 0,
        50 if live_ctx.get('mac') == saved_ctx.get('mac_address') else 0
    ])

    # 3. Dynamic Sb: Adaptive Biometric Score Mapping
    # sensitivity_threshold defines the point where trust hits 0 (e.g., -0.25)
    SENSITIVITY_THRESHOLD = 0.25
    
    if svm_score >= 0.0: 
        sb = 100.0  # Statistical Inlier
    elif svm_score <= -SENSITIVITY_THRESHOLD:
        sb = 0.0    # Outlier beyond recovery
    else: 
        # Linear scaling based on distance. 
        # Example: SVM -0.125 -> Sb = 50.0
        # Example: SVM -0.2475 -> Sb = 1.0
        sb = round(100 * (1 - (abs(svm_score) / SENSITIVITY_THRESHOLD)), 2)

    # 4. Final Weighted Equation: TI = (Sb * 0.6) + (Sc * 0.4)
    ti = round((sb * 0.6) + (sc * 0.4), 2)
    
    # 5. Threshold & Decision Logic
    otp_code = None
    if ti >= 85:
        status = "SUCCESS"
    elif 55 <= ti < 85:
        status = "CHALLENGE"
        otp_code = otp_manager.send_otp(email) 
    else:
        status = "DENIED"

    # 6. Forensic Logging
    _log_to_forensics(username, status, ti, sb, sc, svm_score, live_dna, trained_dna_mean, live_ctx)

    return {
        "status": status,
        "username": username,
        "trust_index": ti,
        "biometric_score": int(sb),
        "context_score": int(sc),
        "otp": otp_code 
    }

def _log_to_forensics(user, status, ti, sb, sc, svm, live, train, ctx):
    """Writes a detailed forensic entry to CSV."""
    file_exists = os.path.isfile(AUDIT_LOG_CSV)
    os.makedirs(os.path.dirname(AUDIT_LOG_CSV), exist_ok=True)

    feature_names = ["CPM", "Backspaces", "Hold_Avg", "Hold_Max", "Hold_Min", "Lat_Avg", "Lat_Max", "Lat_Min", 
                     "Digraph_Avg", "Digraph_Max", "Digraph_Min", "Rel_Avg", "Rel_Max", "Rel_Min"]

    headers = ["Timestamp", "Username", "Status", "TI", "Sb", "Sc", "SVM"]
    for f in feature_names: 
        headers.extend([f"Live_{f}", f"Train_{f}"])
    headers.extend(["Machine_ID", "MAC", "IP", "Host", "Reg_Key"])

    bio_pairs = []
    for i in range(len(feature_names)):
        l_val = live[i] if (live and i < len(live)) else 0
        t_val = train[i] if (train and i < len(train)) else 0
        bio_pairs.extend([round(float(l_val), 3), round(float(t_val), 3)])

    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, status, ti, sb, sc, svm] + \
          bio_pairs + [ctx.get('machine_id'), ctx.get('mac'), ctx.get('ip'), ctx.get('hostname'), ctx.get('reg_key')]

    with open(AUDIT_LOG_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists: 
            writer.writerow(headers)
        writer.writerow(row)