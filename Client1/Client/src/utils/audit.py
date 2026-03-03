import csv
import os
from datetime import datetime
# Updated import path to match your project structure
from Client.src.utils.context import get_contextual_data

def log_audit(user_id, status, score, dna_metrics, device_match):
    """
    Logs every authentication attempt with full biometric and contextual forensic data.
    """
    log_file = 'logs/access_audit.csv'
    os.makedirs('logs', exist_ok=True)
    
    # Gather hardware/network context
    ctx = get_contextual_data()
    
    # 14-Feature set headers
    feature_names = [
        "CPM", "Backspaces", 
        "Hold_Avg", "Hold_Max", "Hold_Min",
        "Lat_Avg", "Lat_Max", "Lat_Min",
        "Digraph_Avg", "Digraph_Max", "Digraph_Min",
        "Rel_Avg", "Rel_Max", "Rel_Min"
    ]

    # Build the CSV Header
    headers = [
        'Timestamp', 'User', 'Status', 'SVM_Score', 'Device_Trusted',
        'IP_Address', 'Machine_UUID', 'MAC_Address'
    ]
    
    # Add Live vs Train columns for every feature
    for f in feature_names:
        headers.extend([f'Live_{f}', f'Train_{f}'])

    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        
        # Build the Data Row
        data_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id, status, score, device_match,
            ctx['ip'], ctx['machine_id'], ctx['mac']
        ]

        # Extract biometric pairs from the dna_metrics dictionary
        # Expected format: dna_metrics = {'live': [14 values], 'train': [14 values]}
        live_list = dna_metrics.get('live', [0]*14)
        train_list = dna_metrics.get('train', [0]*14)

        for l_val, t_val in zip(live_list, train_list):
            data_row.extend([round(float(l_val), 3), round(float(t_val), 3)])
        
        writer.writerow(data_row)