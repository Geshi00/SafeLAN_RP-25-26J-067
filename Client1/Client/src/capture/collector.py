import json, os

def save_enrollment_data(user_id, password, all_samples):
    os.makedirs('data/raw', exist_ok=True)
    file_path = f'data/raw/{user_id}_raw.json'
    data = {"password": password, "samples": all_samples}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return True