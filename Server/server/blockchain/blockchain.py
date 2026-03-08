import time
import json
import os
from .block import Block

BLOCKCHAIN_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "blockchain_data.json")

class Blockchain:
    def __init__(self, authorities):
        self.authorities = authorities
        self.user_roles = {}  # {user_id: 'admin' or 'user'}
        self.pending_transactions = []  # Transactions waiting to be included in a block
        self.max_transactions_per_block = 1  # ⚡ IMMEDIATE MINING
        self.block_creation_interval = 10  # Fallback for time-based mining
        self.last_block_time = time.time()

        # Try to load existing blockchain from disk
        if os.path.exists(BLOCKCHAIN_DATA_FILE):
            print(f"Loading existing blockchain from {BLOCKCHAIN_DATA_FILE}...")
            self.load_from_disk()
        else:
            print("Creating new blockchain...")
            self.chain = [self.create_genesis_block()]
            self.save_to_disk()  # Save genesis block

    def create_genesis_block(self):
        return Block(0, time.time(), [], "0", "GENESIS")

    def get_latest_block(self):
        return self.chain[-1]

    def is_authorized(self, authority_id):
        return authority_id in self.authorities

    def add_block(self, transactions, authority_id):
        if not self.is_authorized(authority_id):
            raise Exception("Unauthorized authority")

        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=self.get_latest_block().hash,
            validator=authority_id
        )
        self.chain.append(block)
        
        # Save to disk after adding block
        self.save_to_disk()

    # Transaction Batching Methods 
    def add_transaction(self, transaction_dict):
        #Add a single transaction to the pending pool. Auto-creates block when conditions are met.
    
        # Validate transaction using smart contract
        from .smart_contracts import file_access_contract
        
        try:
            is_valid = file_access_contract.execute(transaction_dict)
            print(f"[DEBUG] Smart Contract validation: SUCCESS")
        except Exception as e:
            print(f"❌ Smart contract validation error: {e}")
            return False
        
        # Add to pending pool
        self.pending_transactions.append(transaction_dict)
        print(f"✅ Transaction added to pool. Pending: {len(self.pending_transactions)}")
        
        # Save to disk immediately so pending logs aren't lost on restart
        self.save_to_disk()

        # Check if we should create a block
        if self._should_create_block():
            self._create_block_from_pending()
        
        return True
    
    def _should_create_block(self):
        """
        Determine if a new block should be created.
        
        Conditions:
        1. Transaction count reached limit, OR
        2. Time interval passed AND has pending transactions
        """
        # Condition 1: Transaction limit reached
        if len(self.pending_transactions) >= self.max_transactions_per_block:
            print(f"📦 Block creation triggered: Transaction limit reached ({len(self.pending_transactions)})")
            return True
        
        # Condition 2: Time interval passed
        time_elapsed = time.time() - self.last_block_time
        if time_elapsed >= self.block_creation_interval and len(self.pending_transactions) > 0:
            print(f"⏰ Block creation triggered: Time interval ({time_elapsed:.0f}s) passed with {len(self.pending_transactions)} pending")
            return True
        
        return False
    
    def _create_block_from_pending(self, authority_id="ADMIN_01"):
        #Create a new block from pending transactions.
        
        if not self.pending_transactions:
            print("⚠️ No pending transactions to create block")
            return
        
        # Take transactions from pool (up to max)
        transactions_to_include = self.pending_transactions[:self.max_transactions_per_block]
        
        # Remove from pending pool
        self.pending_transactions = self.pending_transactions[self.max_transactions_per_block:]
        
        print(f"🔨 Creating block with {len(transactions_to_include)} transactions")
        
        # Create the block
        self.add_block(transactions_to_include, authority_id)
        
        # Update last block time
        self.last_block_time = time.time()
        
        print(f"✅ Block created. Remaining pending: {len(self.pending_transactions)}")
    
    def force_block_creation(self, authority_id="ADMIN_01"):
        #Manually force creation of a block from pending transactions. Useful for testing or admin operations.
        
        print("🔧 Forcing block creation...")
        self._create_block_from_pending(authority_id)

    # Chain Validation 
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.hash != curr.calculate_hash():
                return False
            if curr.previous_hash != prev.hash:
                return False
        return True
    
    #  Merkle Tree Verification =====
    def verify_transaction_in_block(self, block_index, transaction_index):
        if block_index >= len(self.chain):
            return {
                "valid": False,
                "error": "Block index out of range"
            }
        
        block = self.chain[block_index]
        
        if transaction_index >= len(block.transactions):
            return {
                "valid": False,
                "error": "Transaction index out of range"
            }
        
        # Use Merkle proof for efficient verification
        is_valid = block.verify_transaction(transaction_index)
        
        transaction = block.transactions[transaction_index]
        
        return {
            "valid": is_valid,
            "block_index": block_index,
            "transaction_index": transaction_index,
            "transaction": transaction,
            "merkle_root": block.merkle_root,
            "block_hash": block.hash
        }

    # User Management 
    def register_user(self, user_id, role):
        """Register a user with their role (admin/user)"""
        if role not in ['admin', 'user']:
            raise ValueError("Role must be 'admin' or 'user'")
        self.user_roles[user_id] = role

    # Query Methods - Consolidated


    def get_logs_for_user(self, user_id, requesting_user_id=None, role=None):
        """Return all transactions involving a specific user (sender, receiver, or owner)."""
        all_tx = []
        effective_role = role or (self.user_roles.get(requesting_user_id, 'user') if requesting_user_id else 'user')
        all_sources = [block.transactions for block in self.chain] + [self.pending_transactions]
        for tx_list in all_sources:
            for tx in tx_list:
                if effective_role == 'admin':
                    can_view = True
                else:
                    can_view = (tx.get("sender") == requesting_user_id or
                                tx.get("receiver") == requesting_user_id or
                                tx.get("receiver") == "PUBLIC" or
                                tx.get("file_owner") == requesting_user_id)
                if not can_view:
                    continue
                # Filter to requested user
                if user_id == "PUBLIC":
                    if effective_role == 'admin' or tx.get("receiver") == "PUBLIC":
                        all_tx.append(tx)
                elif (tx.get("sender") == user_id or tx.get("receiver") == user_id or
                        tx.get("file_owner") == user_id):
                    all_tx.append(tx)
        return sorted(all_tx, key=lambda x: x.get("timestamp", 0))

    def get_logs_for_filename(self, filename, requesting_user_id=None, role=None):
        """Return all transactions for a specific filename."""
        all_tx = []
        effective_role = role or (self.user_roles.get(requesting_user_id, 'user') if requesting_user_id else 'user')
        all_sources = [block.transactions for block in self.chain] + [self.pending_transactions]
        for tx_list in all_sources:
            for tx in tx_list:
                if tx.get("filename", "").lower() != filename.lower():
                    continue
                if effective_role == 'admin':
                    can_view = True
                else:
                    can_view = (tx.get("sender") == requesting_user_id or
                                tx.get("receiver") == requesting_user_id or
                                tx.get("receiver") == "PUBLIC" or
                                tx.get("file_owner") == requesting_user_id)
                if can_view:
                    all_tx.append(tx)
        return sorted(all_tx, key=lambda x: x.get("timestamp", 0))

    def get_file_statistics(self, file_hash, requesting_user_id=None):
        
        role = self.user_roles.get(requesting_user_id, 'user') if requesting_user_id else 'user'
        
        stats = {
            "file_hash": file_hash,
            "total_accesses": 0,
            "actions": {},
            "unique_accessors": set(),
            "last_access": None,
            "first_access": None
        }
        
        for block in self.chain:
            for tx in block.transactions:
                if tx["file_hash"] == file_hash:
                    # Check visibility
                    can_view = False
                    if role == 'admin':
                        can_view = True
                    elif (tx["sender"] == requesting_user_id or 
                          tx["receiver"] == requesting_user_id or
                          tx.get("file_owner") == requesting_user_id):
                        can_view = True
                    
                    if not can_view:
                        continue
                    
                    stats["total_accesses"] += 1
                    
                    # Count actions
                    action = tx["action"]
                    stats["actions"][action] = stats["actions"].get(action, 0) + 1
                    
                    # Track unique users
                    stats["unique_accessors"].add(tx["sender"])
                    if tx["receiver"] != tx["sender"]:
                        stats["unique_accessors"].add(tx["receiver"])
                    
                    # Track timestamps
                    timestamp = tx["timestamp"]
                    if stats["last_access"] is None or timestamp > stats["last_access"]:
                        stats["last_access"] = timestamp
                    if stats["first_access"] is None or timestamp < stats["first_access"]:
                        stats["first_access"] = timestamp
        
        # Convert set to list for JSON serialization
        stats["unique_accessors"] = list(stats["unique_accessors"])
        
        return stats

    def get_all_logs(self, requesting_user_id):
        """Only admins can retrieve all logs"""
        if self.user_roles.get(requesting_user_id) != 'admin':
            raise Exception("Unauthorized: Admin access required")
        
        all_logs = []
        for block in self.chain:
            for tx in block.transactions:
                all_logs.append(tx)
        return all_logs

    def get_full_chain(self):
        return [block.__dict__ for block in self.chain]

    # PERSISTENCE METHODS
    
    def save_to_disk(self):
        """Save blockchain to disk"""
        try:
            data = {
                "chain": [],
                "user_roles": self.user_roles,
                "pending_transactions": getattr(self, 'pending_transactions', []),
                "last_block_time": getattr(self, 'last_block_time', time.time())
                
            }
            
            # Serialize each block
            for block in self.chain:
                block_data = {
                    "index": block.index,
                    "timestamp": block.timestamp,
                    "transactions": block.transactions,
                    "transaction_count": getattr(block, 'transaction_count', len(block.transactions)),  # NEW
                    "merkle_root": getattr(block, 'merkle_root', None),  # NEW
                    "previous_hash": block.previous_hash,
                    "validator": block.validator,
                    "hash": block.hash
                }
                data["chain"].append(block_data)
            
            # Write to file
            with open(BLOCKCHAIN_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            # print(f"✅ Blockchain saved ({len(self.chain)} blocks)")
        except Exception as e:
            print(f"✗ Error saving blockchain: {e}")

    def load_from_disk(self):
        """Load blockchain from disk"""
        try:
            with open(BLOCKCHAIN_DATA_FILE, 'r') as f:
                data = json.load(f)
            
            # Restore user roles
            self.user_roles = data.get("user_roles", {})
            
            # ===== NEW: Restore pending transactions =====
            self.pending_transactions = data.get("pending_transactions", [])
            self.last_block_time = data.get("last_block_time", time.time())
            
            # Initialize if not present (for backwards compatibility)
            if not hasattr(self, 'max_transactions_per_block'):
                self.max_transactions_per_block = 50
            if not hasattr(self, 'block_creation_interval'):
                self.block_creation_interval = 60
            
            
            # Standardize path back to Server directory per user constraint
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.data_file = os.path.join(base_dir, "blockchain_data.json")
            # Restore chain
            self.chain = []
            for block_data in data["chain"]:
                block = Block(
                    index=block_data["index"],
                    timestamp=block_data["timestamp"],
                    transactions=block_data["transactions"],
                    previous_hash=block_data["previous_hash"],
                    validator=block_data["validator"]
                )
                # Use the stored hash (important for consistency)
                block.hash = block_data["hash"]
                
                # Restore merkle data 
                if 'merkle_root' in block_data:
                    block.merkle_root = block_data['merkle_root']
                if 'transaction_count' in block_data:
                    block.transaction_count = block_data['transaction_count']
                
                self.chain.append(block)
            
            print(f"✅ Blockchain loaded: {len(self.chain)} blocks, {self.count_transactions()} transactions")
            
            # Show pending transactions 
            if self.pending_transactions:
                print(f"📋 Loaded {len(self.pending_transactions)} pending transactions")
            
        except Exception as e:
            print(f"✗ Error loading blockchain: {e}")
            # If loading fails, create new blockchain
            self.chain = [self.create_genesis_block()]
            self.pending_transactions = []
            self.last_block_time = time.time()

    def count_transactions(self):
        """Count total transactions in blockchain"""
        total = 0
        for block in self.chain:
            total += len(block.transactions)
        return total

    def clear_blockchain(self):
        """Clear blockchain and start fresh (use with caution!)"""
        self.chain = [self.create_genesis_block()]
        self.user_roles = {}
        self.save_to_disk()
        print("✓ Blockchain cleared and reset to genesis block")
