# proxmox_manager/proxmox_connection.py
import os
from proxmoxer import ProxmoxAPI

def get_proxmox():
    """
    Creates and returns a ProxmoxAPI object.
    Adjust host/user/pass or read from environment variables as needed.
    """
    PROXMOX_HOST = os.getenv("PROXMOX_HOST", "192.168.0.21")
    PROXMOX_USER = os.getenv("PROXMOX_USER", "root@pam")
    PROXMOX_PASS = os.getenv("PROXMOX_PASS", "151677")
    return ProxmoxAPI(PROXMOX_HOST, user=PROXMOX_USER, password=PROXMOX_PASS, verify_ssl=False)
