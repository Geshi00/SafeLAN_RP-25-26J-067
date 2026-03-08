import hashlib
import json

class MerkleTree:
    """
    Merkle tree implementation for transaction verification.
    A Merkle tree is a binary tree where:
    - Leaves are hashes of transactions
    - Parents are hashes of their children
    - Root is the hash of the entire tree
    """
    def __init__(self, transactions):
        self.transactions = transactions
        self.tree = self._build_tree()
        self.root = self.tree[0][0] if self.tree else None
    
    def _hash(self, data):
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(str(data).encode()).hexdigest()
    
    def _build_tree(self):
        if not self.transactions:
            # Empty tree - return hash of empty string
            return [[self._hash("")]]
        
        # Level 0: Hash all transactions (leaf nodes)
        current_level = [self._hash(tx) for tx in self.transactions]
        tree = [current_level]
        
        # Build tree upwards until we reach root
        while len(current_level) > 1:
            next_level = []
            
            # Pair up hashes and combine them
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # If odd number of nodes, duplicate the last one
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                
                # Parent = hash(left + right)
                combined = left + right
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)
            
            tree.insert(0, next_level)  # Insert at beginning (root at index 0)
            current_level = next_level
        
        return tree
    
    def get_proof(self, transaction_index):
        """
        Generate Merkle proof for a specific transaction.
        A Merkle proof is the list of hashes needed to reconstruct
        the path from a transaction to the root.
        """
        if transaction_index >= len(self.transactions):
            return None
        
        proof = []
        index = transaction_index
        
        # Traverse tree from leaf to root
        for level in reversed(self.tree[1:]):  # Skip root level
            # Find sibling index
            sibling_index = index + 1 if index % 2 == 0 else index - 1
            
            if sibling_index < len(level):
                proof.append({
                    "hash": level[sibling_index],
                    "position": "right" if index % 2 == 0 else "left"
                })
            
            # Move up to parent
            index = index // 2
        
        return proof
    
    @staticmethod
    def verify_proof(transaction, merkle_root, proof):
        # Start with hash of transaction
        tree = MerkleTree([])
        current_hash = tree._hash(transaction)
        
        # Reconstruct path to root
        for step in proof:
            if step["position"] == "right":
                # Sibling is on right, we're on left
                combined = current_hash + step["hash"]
            else:
                # Sibling is on left, we're on right
                combined = step["hash"] + current_hash
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        # Compare reconstructed root with expected root
        return current_hash == merkle_root
    
    def __str__(self):
        """String representation for debugging"""
        return f"MerkleTree(root={self.root[:8]}..., tx_count={len(self.transactions)})"