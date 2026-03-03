from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, json, pandas as pd
import numpy as np
import joblib
from datetime import datetime

# Internal Server-Side Imports
from server.database import (
    retrieve_user_identity, init_db, save_enrollment, 
    sync_file_metadata, get_visible_files, remove_file_metadata
)
from server.services.trust_engine import calculate_trust_index

app = FastAPI()

# Enable cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_BASE = os.path.join(BASE_DIR, "storage", "user_models")
VAULT_DIR = os.path.join(BASE_DIR, "vault")

# --- GLOBAL MODEL CACHE ---
# Stores loaded models in RAM to prevent "Read timed out" errors
model_cache = {}

@app.on_event("startup")
def startup():
    os.makedirs(STORAGE_BASE, exist_ok=True)
    os.makedirs(VAULT_DIR, exist_ok=True)
    init_db()

@app.get("/health")
async def health():
    return {"status": "online", "server_time": datetime.now().isoformat()}

@app.post("/auth/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    dna_means: str = Form(...),
    context: str = Form(...),
    model: UploadFile = File(...),
    scaler: UploadFile = File(...)
):
    try:
        ctx_dict = json.loads(context)
        means_list = json.loads(dna_means)
        
        db_ctx = {
            "hw_uuid": ctx_dict.get('machine_id', ctx_dict.get('uuid', 'Unknown')),
            "mac_address": ctx_dict.get('mac', 'Unknown'),
            "hostname": ctx_dict.get('hostname', 'Unknown'),
            "reg_key": ctx_dict.get('reg_key', 'SECURE_GATEWAY_V1'),
            "registered_subnet": ".".join(str(ctx_dict.get('ip', '127.0.0.1')).split('.')[:-1]) + ".0"
        }

        user_path = os.path.join(STORAGE_BASE, username)
        os.makedirs(user_path, exist_ok=True)
        
        # Save files
        with open(os.path.join(user_path, "svm.pkl"), "wb") as f:
            shutil.copyfileobj(model.file, f)
        with open(os.path.join(user_path, "scaler.pkl"), "wb") as f:
            shutil.copyfileobj(scaler.file, f)

        save_enrollment(username, password, email, means_list, db_ctx)
        
        # Invalidate cache for this user if they are re-registering
        if username in model_cache:
            del model_cache[username]
            
        return {"status": "SUCCESS"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/auth/verify")
async def verify(request: Request):
    data = await request.json()
    username = data.get('username')
    
    identity = retrieve_user_identity(username)
    if not identity: 
        return {"status": "DENIED", "trust_index": 0}

    try:
        # Load from cache or disk
        if username not in model_cache:
            user_path = os.path.join(STORAGE_BASE, username)
            model_cache[username] = {
                "svm": joblib.load(os.path.join(user_path, "svm.pkl")),
                "scaler": joblib.load(os.path.join(user_path, "scaler.pkl"))
            }
        
        cache = model_cache[username]
        live_dna = np.array(data['dna_features']).reshape(1, -1)
        scaled_dna = cache["scaler"].transform(live_dna)
        svm_score = float(cache["svm"].decision_function(scaled_dna)[0])
        
        print(f"[DEBUG] {username} SVM Distance (Cached): {svm_score:.4f}")
    except Exception as e:
        print(f"Verify Logic Error: {e}")
        svm_score = -1.0

    trust_result = calculate_trust_index(
        username=username, 
        typed_pw=data['password'],
        stored_pw_hash=identity['password_hash'], 
        email=identity['email'],
        svm_score=svm_score,
        live_dna=data['dna_features'], 
        trained_dna_mean=identity['dna_means'],
        live_ctx=data['context'], 
        saved_ctx=identity['device_context']
    )

    trust_result["svm_score"] = svm_score
    return trust_result

# --- File System Endpoints ---
@app.get("/files/list")
async def list_files(user: str = "PUBLIC"):
    return get_visible_files(user.upper())

@app.get("/files/download/{filename}")
async def download_shared_file(filename: str):
    file_path = os.path.join(VAULT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    return {"status": "NOT_FOUND"}, 404

@app.post("/files/upload")
async def upload_shared_file(file: UploadFile = File(...), owner: str = Form(...), target: str = Form("PUBLIC")):
    file_path = os.path.join(VAULT_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    size_str = f"{round(os.path.getsize(file_path)/1024, 1)} KB"
    date_str = datetime.now().strftime('%Y-%m-%d')
    sync_file_metadata(file.filename, owner.upper(), target.upper(), size_str, date_str)
    return {"status": "SUCCESS"}

@app.delete("/files/delete/{filename}")
async def delete_file(filename: str):
    path = os.path.join(VAULT_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    remove_file_metadata(filename)
    return {"status": "SUCCESS"}