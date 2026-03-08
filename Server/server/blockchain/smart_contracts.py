import time
from datetime import datetime, timedelta

class FileAccessSmartContract:
    """
    - Role-based permissions
    - Ownership validation
    - Time-based rules
    - Rate limiting
    """ 
    
    def __init__(self, role_permissions):
        """     
         'admin': ['VIEW', 'OPEN', 'AUDIT'],
         'user': ['VIEW', 'OPEN', 'MODIFY', 'SHARE', 'DELETE']
        """
        self.role_permissions = role_permissions
        
        # Advanced features (can be enabled/disabled)
        self.enable_time_restrictions = False
        self.enable_rate_limiting = False
        
        # Time restrictions (business hours only)
        self.allowed_hours = {
            'start': 8,  # 8 AM
            'end': 18    # 6 PM
        }
        
        # Rate limiting (max actions per user per hour)
        self.rate_limit = {
            'SHARE': 100,
            'MODIFY': 50,
            'DELETE': 20
        }
        self.user_action_counts = {}  # {user_id: {action: [(timestamp, count)]}}
        
        # Violation tracking
        self.violations = []
    
    def validate_transaction(self, transaction):
        #      Validate a transaction before it's added to the blockchain.
        
        try:
            sender = transaction.get("sender")
            role = transaction.get("role")
            action = transaction.get("action")
            file_owner = transaction.get("file_owner")
            file_hash = transaction.get("file_hash")
            timestamp = transaction.get("timestamp", time.time())
            receiver = transaction.get("receiver")
            
            print(f"[CONTRACT] Validating: action={action}, sender={sender}, role={role}, file_owner={file_owner}, receiver={receiver}")
           
            # Check required fields
            if not sender:
                print("[CONTRACT] REJECT: Missing sender")
                return False, "Missing sender in transaction"
            
            if not role:
                print("[CONTRACT] REJECT: Missing role")
                return False, "Missing role in transaction"
            
            if not action:
                print("[CONTRACT] REJECT: Missing action")
                return False, "Missing action in transaction"
            
            if not file_owner:
                print("[CONTRACT] REJECT: Missing file_owner")
                return False, "Missing file_owner in transaction"
            
            if not file_hash:
                print("[CONTRACT] REJECT: Missing file_hash")
                return False, "Missing file_hash in transaction"
            
            # Role-based permission check
            allowed_actions = self.role_permissions.get(role, [])
            if action not in allowed_actions:
                self._record_violation(sender, action, f"Action '{action}' not allowed for role '{role}'")
                print(f"[CONTRACT] REJECT: Action '{action}' not allowed for role '{role}'. Allowed: {allowed_actions}")
                return False, f"Action '{action}' not allowed for role '{role}'"
            
            # Ownership rule - only file owner can modify
            if action == "MODIFY" and sender != file_owner:
                self._record_violation(sender, action, "Non-owner attempted to modify file")
                print(f"[CONTRACT] REJECT: MODIFY ownership check failed. sender={sender}, file_owner={file_owner}")
                return False, "Only the file owner can modify the file"
            
            # Ownership rule - only file owner can delete
            if action == "DELETE" and sender != file_owner:
                self._record_violation(sender, action, "Non-owner attempted to delete file")
                print(f"[CONTRACT] REJECT: DELETE ownership check failed. sender={sender}, file_owner={file_owner}")
                return False, "Only the file owner can delete the file"
            
            # Admin safety rule - admins can ONLY view/audit, not modify or share
            if role == "admin" and action in ["MODIFY", "SHARE", "DELETE"]:
                self._record_violation(sender, action, "Admin attempted restricted action")
                print(f"[CONTRACT] REJECT: Admin attempted restricted action: {action}")
                return False, "Admins can only view and audit, not modify, share, or delete files"
            
            # Time-based restrictions
            if self.enable_time_restrictions:
                is_valid, message = self._validate_time_restriction(timestamp)
                if not is_valid:
                    self._record_violation(sender, action, message)
                    return False, message
            
            # Rate limiting 
            if self.enable_rate_limiting:
                is_valid, message = self._validate_rate_limit(sender, action, timestamp)
                if not is_valid:
                    self._record_violation(sender, action, message)
                    return False, message
            
            # Prevent sharing to self
            if action == "SHARE" and receiver == sender:
                print(f"[CONTRACT] REJECT: Cannot share with yourself")
                return False, "Cannot share file with yourself"
            
            # Validate receiver exists 
            if receiver and not receiver.strip():
                print(f"[CONTRACT] REJECT: Invalid receiver")
                return False, "Invalid receiver ID"
            
            # All validations passed
            print(f"[DEBUG] Contract: Validation PASSED for {action} by {sender} on {receiver}")
            return True, "Transaction valid"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def execute(self, transaction):
        """
        Execute validation and raise exception if invalid.
        This integrates with the blockchain's add_block method.
        """
        is_valid, message = self.validate_transaction(transaction)
        
        if not is_valid:
            raise Exception(f"Smart contract validation failed: {message}")
        
        return True
    
    # ADVANCED VALIDATION METHODS 
    def _validate_time_restriction(self, timestamp):
        """
        Validate that transaction is within allowed business hours.
        """
        dt = datetime.fromtimestamp(timestamp)
        hour = dt.hour
        
        # Check if within business hours
        if hour < self.allowed_hours['start'] or hour >= self.allowed_hours['end']:
            return False, f"File operations only allowed between {self.allowed_hours['start']}:00 and {self.allowed_hours['end']}:00"
        
        # Check if weekend (optional - commented out)
        # if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        #     return False, "File operations not allowed on weekends"
        
        return True, "Time validation passed"
    
    def _validate_rate_limit(self, user_id, action, timestamp):
        """
        Validate that user hasn't exceeded rate limit.
        """
        # Get rate limit for this action
        limit = self.rate_limit.get(action, float('inf'))
        
        # Initialize user tracking if needed
        if user_id not in self.user_action_counts:
            self.user_action_counts[user_id] = {}
        
        if action not in self.user_action_counts[user_id]:
            self.user_action_counts[user_id][action] = []
        
        # Clean old entries (older than 1 hour)
        one_hour_ago = timestamp - 3600
        self.user_action_counts[user_id][action] = [
            ts for ts in self.user_action_counts[user_id][action]
            if ts > one_hour_ago
        ]
        
        # Check if limit exceeded
        current_count = len(self.user_action_counts[user_id][action])
        
        if current_count >= limit:
            return False, f"Rate limit exceeded: {current_count}/{limit} {action} actions in last hour"
        
        # Record this action
        self.user_action_counts[user_id][action].append(timestamp)
        
        return True, "Rate limit check passed"
    
    def _record_violation(self, user_id, action, reason):
        """Record a validation violation for audit purposes."""
        violation = {
            "timestamp": time.time(),
            "user_id": user_id,
            "action": action,
            "reason": reason
        }
        self.violations.append(violation)
        
        # Keep only last 1000 violations to prevent memory issues
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]
    
    # CONFIGURATION METHODS
    def enable_advanced_features(self, time_restrictions=False, rate_limiting=False, size_limits=False):
        """Enable/disable advanced validation features."""
        self.enable_time_restrictions = time_restrictions
        self.enable_rate_limiting = rate_limiting
        
        print(f"Advanced features configured:")
        print(f"  - Time restrictions: {time_restrictions}")
        print(f"  - Rate limiting: {rate_limiting}")
    
    def set_business_hours(self, start_hour, end_hour):
        """Set allowed business hours."""
        self.allowed_hours = {
            'start': start_hour,
            'end': end_hour
        }
        print(f"Business hours set: {start_hour}:00 - {end_hour}:00")
    
    def set_rate_limits(self, limits):
        """Set rate limits for actions."""
        self.rate_limit.update(limits)
        print(f"Rate limits updated: {limits}")
    
    def get_violations(self, user_id=None, limit=100):
        """Get recorded violations."""
        violations = self.violations
        
        if user_id:
            violations = [v for v in violations if v['user_id'] == user_id]
        
        return violations[-limit:]
    
    def clear_violations(self):
        """Clear all recorded violations"""
        self.violations = []
        print("Violations cleared")


# Default role permissions for SafeLAN
DEFAULT_ROLE_PERMISSIONS = {
    'admin': ['OPEN', 'AUDIT'],
    'user': ['OPEN', 'MODIFY', 'SHARE', 'DELETE', 'UPLOAD', 'DOWNLOAD']
}

# Create default contract instance
file_access_contract = FileAccessSmartContract(DEFAULT_ROLE_PERMISSIONS) 
