import hashlib
import json
from .merkle_tree import MerkleTree

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, validator):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.validator = validator
        self.merkle_tree = MerkleTree(transactions)
        self.merkle_root = self.merkle_tree.root
        self.transaction_count = len(transactions)
        
        # Calculate block hash (includes merkle root)
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,  # NEW
            "transaction_count": self.transaction_count,  # NEW
            "previous_hash": self.previous_hash,
            "validator": self.validator
        }, sort_keys=True)

        return hashlib.sha256(block_data.encode()).hexdigest()
    
    def verify_transaction(self, transaction_index):
        #Verify a specific transaction using Merkle proof.
        if transaction_index >= len(self.transactions):
            return False
        
        transaction = self.transactions[transaction_index]
        proof = self.merkle_tree.get_proof(transaction_index)
        
        return MerkleTree.verify_proof(transaction, self.merkle_root, proof)
    
    def to_dict(self):
        #Serialize block to dictionary. Includes all block data including Merkle root.
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "transaction_count": self.transaction_count,
            "merkle_root": self.merkle_root,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "hash": self.hash
        }