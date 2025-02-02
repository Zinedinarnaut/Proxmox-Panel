# proxmox_manager/csrf_handler.py

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkCookie

class CSRFHandler:
    """
    A helper class that retrieves and stores the Proxmox ticket (PVEAuthCookie)
    and CSRF token (CSRFPreventionToken) from a proxmoxer ProxmoxAPI object.

    Usage:
        from proxmox_manager.csrf_handler import CSRFHandler
        handler = CSRFHandler(proxmox)
        # Then handler.ticket, handler.csrf
        # Optionally inject cookie into QWebEngineView
    """

    def __init__(self, proxmox):
        self.proxmox = proxmox
        self.ticket = None
        self.csrf = None
        self.retrieve_tokens()

    def retrieve_tokens(self):
        """
        Attempts to call proxmox.get_tokens(), storing ticket and csrf in self.
        Handles both dict-based and tuple-based returns.
        """
        tokens = self.proxmox.get_tokens()

        if isinstance(tokens, dict):
            # Newer proxmoxer versions
            self.ticket = tokens.get("ticket", None)
            self.csrf = tokens.get("CSRFPreventionToken", None)
        elif isinstance(tokens, tuple) and len(tokens) >= 2:
            # Some proxmoxer versions return (ticket, csrf)
            self.ticket = tokens[0]
            self.csrf = tokens[1]
        else:
            # No recognized tokens
            self.ticket = None
            self.csrf = None

    def inject_cookie(self, webengineview):
        """
        Injects the PVEAuthCookie into a PyQt6 QWebEngineView,
        so the embedded browser session is authenticated.

        :param webengineview: The QWebEngineView instance where you want to inject the cookie.
        """
        if not self.ticket:
            # No ticket, nothing to inject
            return

        profile = webengineview.page().profile()
        cookie_store = profile.cookieStore()

        # Example domain usage: if your proxmox is '192.168.0.21', that must match the host in the noVNC URL
        # Adjust domain below to your actual Proxmox host domain or IP
        domain = self.proxmox.host

        cookie = QNetworkCookie()
        cookie.setName(b"PVEAuthCookie")
        cookie.setValue(self.ticket.encode("utf-8"))
        cookie.setDomain(domain)
        cookie.setPath("/")
        cookie.setSecure(False)
        cookie.setHttpOnly(False)

        # The URL must match the same scheme/host used when you load the console
        url = QUrl(f"https://{domain}:8006")

        # Add cookie
        cookie_store.setCookie(cookie, url)

    def get_headers(self):
        """
        Example method returning headers for manual requests,
        if you want to do custom calls. The CSRF token must be used
        as 'CSRFPreventionToken' in the header if the method is not GET.

        :return: dict of { 'CSRFPreventionToken': '...' } if available
        """
        headers = {}
        if self.csrf:
            headers["CSRFPreventionToken"] = self.csrf
        return headers

    def is_authenticated(self):
        """
        :return: True if we have a ticket, else False
        """
        return bool(self.ticket)
