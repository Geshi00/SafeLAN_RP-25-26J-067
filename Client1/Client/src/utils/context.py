import subprocess
import socket
import uuid

def get_contextual_data():
    """
    Captures hardware and network identity anchors for multi-factor trust.
    """
    # 1. Hardware ID (Machine GUID via PowerShell)
    try:
        cmd = 'powershell.exe (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Cryptography").MachineGuid'
        machine_uuid = subprocess.check_output(cmd, shell=True).decode().strip()
    except:
        machine_uuid = "unknown_device"
    
    # 2. Network Context (IP Address)
    try:
        ip_addr = socket.gethostbyname(socket.gethostname())
    except:
        ip_addr = "127.0.0.1"

    # 3. Physical Hardware Anchor (MAC Address)
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                for ele in range(0, 8*6, 8)][::-1])
    except:
        mac = "00:00:00:00:00:00"
        
    return {
        "machine_id": machine_uuid, 
        "ip": ip_addr, 
        "mac": mac,
        "hostname": socket.gethostname()
    }