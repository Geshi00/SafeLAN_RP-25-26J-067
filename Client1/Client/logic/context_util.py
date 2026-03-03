import uuid
import socket
import winreg # Required for the SafeLAN Registry Key
import platform

def get_local_context():
    """Captures the 5 data points required for the Sc calculation."""
    ctx = {
        "uuid": str(uuid.getnode()), # Logical UUID
        "mac": get_mac_address(),    # Physical NIC Address
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "reg_key": get_safelan_registry_key()
    }
    return ctx

def get_mac_address():
    # Returns formatted MAC address for logging
    return ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0,8*6,8)][::-1])

def get_safelan_registry_key():
    """Retrieves the hidden SafeLAN key from the Windows Registry."""
    try:
        # Looking in HKEY_CURRENT_USER\Software\SafeLAN
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\SafeLAN")
        value, _ = winreg.QueryValueEx(key, "DeviceToken")
        return value
    except Exception:
        return "NOT_FOUND"