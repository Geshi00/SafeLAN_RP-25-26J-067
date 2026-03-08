import time
import hashlib

class Transaction:
    def __init__(self, file_hash, sender, receiver, action, role, file_owner, filename=None):
        self.file_hash = file_hash
        self.filename = filename  
        self.sender = sender
        self.receiver = receiver
        self.action = action
        self.role = role
        self.file_owner = file_owner
        self.timestamp = time.time()
        self.tx_id = self.generate_tx_id()

    def generate_tx_id(self):
        raw = f"{self.file_hash}{self.sender}{self.timestamp}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self):
        return {
            "tx_id": self.tx_id,
            "file_hash": self.file_hash,
            "filename": self.filename, 
            "sender": self.sender,
            "receiver": self.receiver,
            "action": self.action,
            "role": self.role,
            "file_owner": self.file_owner,
            "timestamp": self.timestamp
        }
