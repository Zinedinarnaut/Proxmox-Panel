# proxmox_manager/proxmox_connection.py
import os
from proxmoxer import ProxmoxAPI

def get_proxmox():
    """
    Creates and returns a ProxmoxAPI object.
    Adjust host/user/pass or read from environment variables as needed.
    """
    PROXMOX_HOST = os.getenv("PROXMOX_HOST", "YOUR_IP")
    PROXMOX_USER = os.getenv("PROXMOX_USER", "root@pam")
    PROXMOX_PASS = os.getenv("PROXMOX_PASS", "YOUR_PASSWORD")
    return ProxmoxAPI(PROXMOX_HOST, user=PROXMOX_USER, password=PROXMOX_PASS, verify_ssl=False)
