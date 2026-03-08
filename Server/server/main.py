from fastapi import FastAPI, Request, UploadFile, File, Form
# Version: 1.0.1 (Role Propagation Fix)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, json, pandas as pd, time
import numpy as np
import joblib, hashlib
from datetime import datetime
import hashlib

# Internal Server-Side Imports
from server.database import (
    retrieve_user_identity, init_db, save_enrollment, 
    sync_file_metadata, get_visible_files, remove_file_metadata,
    get_all_usernames, get_all_filenames, get_file_metadata
)
from server.services.trust_engine import calculate_trust_index

# --- BLOCKCHAIN INTEGRATION ---
from server.blockchain import Blockchain, Transaction, Authority

# Initialize Blockchain with a default admin authority
admin_auth = Authority("ADMIN_01", "SafeLAN Central Authority")
blockchain = Blockchain(authorities={admin_auth.authority_id: admin_auth.to_dict()})
blockchain.register_user("ADMIN_01", "admin")

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
    
    # Mine any pending transactions that became overdue while the server was offline
    if blockchain.pending_transactions:
        time_since_last_block = time.time() - blockchain.last_block_time
        print(f"[STARTUP] Found {len(blockchain.pending_transactions)} pending transactions. "
              f"Time since last block: {time_since_last_block:.0f}s")
        if time_since_last_block >= blockchain.block_creation_interval:
            print("[STARTUP] Mining overdue pending transactions...")
            blockchain.force_block_creation(authority_id="ADMIN_01")
        else:
            print(f"[STARTUP] Transactions not yet overdue. Will be mined in {blockchain.block_creation_interval - time_since_last_block:.0f}s")

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
async def download_shared_file(filename: str, user: str = "Unknown", role: str = "user", action: str = "DOWNLOAD"):
    file_path = os.path.join(VAULT_DIR, filename)
    if os.path.exists(file_path):
        try:
            # Determine actual receiver and owner from database
            receiver = user.upper()
            owner = user.upper()  # Default to requesting user, not "VAULT"
            meta = get_file_metadata(filename)
            if meta:
                owner = meta['owner']
                # If target is PUBLIC, record as PUBLIC in audit logs
                if meta['target_user'] == 'PUBLIC':
                    receiver = "PUBLIC"
                print(f"[DEBUG] {action}: File={filename}, Owner={owner}, Target={meta['target_user']}, Receiver={receiver}")
            else:
                print(f"[DEBUG] {action}: File {filename} NOT found in DB, using sender as owner")

            # Record blockchain transaction
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            tx = Transaction(
                file_hash=file_hash,
                sender=user.upper(),
                receiver=receiver,
                action=action.upper(),
                role=role,
                file_owner=owner,
                filename=filename
            )
            result = blockchain.add_transaction(tx.to_dict())
            print(f"[DEBUG] Blockchain add result: {result} for action={action.upper()}")
            if not result:
                print(f"[WARNING] Blockchain REJECTED {action} for {filename}")
        except Exception as tx_err:
            print(f"[BLOCKCHAIN ERROR] Failed to record {action}: {tx_err}")
        
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    return {"status": "NOT_FOUND"}, 404

@app.post("/files/upload")
async def upload_shared_file(file: UploadFile = File(...), owner: str = Form(...), role: str = Form("user"), target: str = Form("PUBLIC")):
    file_path = os.path.join(VAULT_DIR, file.filename)
    action = "MODIFY" if os.path.exists(file_path) else "UPLOAD"
    
    # Determine original owner to enforce smart contract ownership rules
    original_owner = owner.upper()
    meta = get_file_metadata(file.filename)
    if meta:
        original_owner = meta['owner']
        print(f"[DEBUG] Modification detected for {file.filename}. Original owner: {original_owner}")

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    size_str = f"{round(os.path.getsize(file_path)/1024, 1)} KB"
    date_str = datetime.now().strftime('%Y-%m-%d')
    sync_file_metadata(file.filename, owner.upper(), target.upper(), size_str, date_str)
    
    try:
        # Record blockchain transaction
        print(f"[DEBUG] Recording {action} to blockchain for {file.filename}...")
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        tx = Transaction(
            file_hash=file_hash,
            sender=owner.upper(),
            receiver=target.upper(),
            action=action,
            role=role,
            file_owner=original_owner,
            filename=file.filename
        )
        success = blockchain.add_transaction(tx.to_dict())
        if success:
            print(f"[DEBUG] Successfully recorded {action} for {file.filename}")
        else:
            print(f"[DEBUG] Blockhain rejected {action} for {file.filename} (Validation failed)")
    except Exception as tx_err:
        print(f"[BLOCKCHAIN ERROR] Failed to record upload/modify: {tx_err}")
    
    return {"status": "SUCCESS"}

@app.delete("/files/delete/{filename}")
async def delete_file(filename: str, user: str = "Unknown", role: str = "user"):
    path = os.path.join(VAULT_DIR, filename)
    if os.path.exists(path):
        try:
            # NEW: Determine actual owner/target for DELETE record
            file_owner = user.upper()
            target_user = "SYSTEM"
            try:
                from server.database import DB_PATH
                import sqlite3
                conn = sqlite3.connect(DB_PATH, timeout=10)
                cur = conn.cursor()
                cur.execute("SELECT owner, target_user FROM shared_files WHERE filename = ?", (filename,))
                row = cur.fetchone()
                if row:
                    file_owner = row[0]
                    target_user = row[1]
                conn.close()
            except: pass

            # Record blockchain transaction before deletion
            file_hash = hashlib.sha256(filename.encode()).hexdigest() 
            tx = Transaction(
                file_hash=file_hash,
                sender=user.upper(),
                receiver=target_user,
                action="DELETE",
                role=role,
                file_owner=file_owner,
                filename=filename
            )
            blockchain.add_transaction(tx.to_dict())
            print(f"[DEBUG] Recorded DELETE for {filename} (Target: {target_user})")
        except Exception as tx_err:
            print(f"[BLOCKCHAIN ERROR] Failed to record delete: {tx_err}")
        
        os.remove(path)
    remove_file_metadata(filename)
    return {"status": "SUCCESS"}

@app.get("/logs/user/{user_id}")
async def get_user_logs(user_id: str, requesting_user_id: str = "Unknown", role: str = None):
    print(f"[DEBUG] Fetching logs for user: {user_id} (Requester: {requesting_user_id}, Role: {role})")
    logs = blockchain.get_logs_for_user(user_id.upper(), requesting_user_id.upper(), role)
    print(f"[DEBUG] Found {len(logs)} logs")
    return logs

@app.get("/logs/filename/{filename}")
async def get_file_logs(filename: str, requesting_user_id: str = "Unknown", role: str = None):
    print(f"[DEBUG] Fetching logs for filename: {filename} (Requester: {requesting_user_id}, Role: {role})")
    logs = blockchain.get_logs_for_filename(filename, requesting_user_id.upper(), role)
    print(f"[DEBUG] Found {len(logs)} logs")
    return logs
    
@app.get("/users/all")
async def list_all_users():
    return get_all_usernames()

@app.get("/files/all")
async def list_all_files():
    return get_all_filenames()

@app.get("/blockchain/stats")
async def get_blockchain_stats():
    return {
        "total_blocks": len(blockchain.chain),
        "total_transactions": blockchain.count_transactions() + len(blockchain.pending_transactions)
    }
