import sys, subprocess
from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)

class VNCTab(QWidget):
    """
    Demonstrates opening a Proxmox VM's noVNC console:
    - In-app (embedded QWebEngineView)
    - External browser

    Uses a CSRF/token handler (optional) to inject PVEAuthCookie to avoid white screens.
    """

    def __init__(self, proxmox, csrf_handler=None):
        """
        :param proxmox: The ProxmoxAPI connection from proxmoxer
        :param csrf_handler: An optional object providing .ticket and .inject_cookie()
                             If omitted, we rely on external noVNC authentication or may see white screen.
        """
        super().__init__()
        self.proxmox = proxmox
        self.csrf_handler = csrf_handler  # e.g., an instance of CSRFHandler
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Row 1: Node and VM ID
        input_layout = QHBoxLayout()
        self.node_input = QLineEdit()
        self.node_input.setPlaceholderText("Node (e.g. pve)")
        input_layout.addWidget(self.node_input)

        self.vmid_input = QLineEdit()
        self.vmid_input.setPlaceholderText("VM ID (e.g. 101)")
        input_layout.addWidget(self.vmid_input)
        layout.addLayout(input_layout)

        # Row 2: Buttons
        btn_layout = QHBoxLayout()
        self.open_inapp_btn = QPushButton("Open In-App VNC")
        self.open_inapp_btn.clicked.connect(self.open_inapp_vnc)
        btn_layout.addWidget(self.open_inapp_btn)

        self.open_ext_btn = QPushButton("Open External VNC")
        self.open_ext_btn.clicked.connect(self.open_external_vnc)
        btn_layout.addWidget(self.open_ext_btn)
        layout.addLayout(btn_layout)

        # QWebEngineView for embedded console
        self.vnc_view = QWebEngineView()
        layout.addWidget(self.vnc_view)

        self.setLayout(layout)

        # Optional: If you want to ignore SSL errors (e.g., self-signed cert),
        # that is advanced code involving QWebEnginePage or a custom interceptor.
        # For demonstration, we do not show that here.

    def open_inapp_vnc(self):
        node = self.node_input.text().strip()
        vmid = self.vmid_input.text().strip()
        if not vmid.isdigit():
            QMessageBox.warning(self, "Warning", "Please enter a valid numeric VM ID.")
            return

        try:
            # 1) Create a VNC proxy session
            result = self.proxmox.nodes(node).qemu(vmid).vncproxy.post()
            port = result["port"]
            host = self.proxmox.host  # e.g., "192.168.0.21" or "pve.local"
            noVNC_url = f"https://{host}:8006/?console=kvm&novnc=1&vmid={vmid}&node={node}&port={port}"

            # 2) If we have a CSRF handler with a valid PVEAuthCookie, inject it
            if self.csrf_handler and self.csrf_handler.ticket:
                self.csrf_handler.inject_cookie(self.vnc_view)  # places PVEAuthCookie in QWebEngineView

            # 3) Load the noVNC URL in-app
            self.vnc_view.setUrl(QUrl(noVNC_url))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open in-app VNC: {e}")

    def open_external_vnc(self):
        node = self.node_input.text().strip()
        vmid = self.vmid_input.text().strip()
        if not vmid.isdigit():
            QMessageBox.warning(self, "Warning", "Please enter a valid numeric VM ID.")
            return

        try:
            result = self.proxmox.nodes(node).qemu(vmid).vncproxy.post()
            port = result["port"]
            host = self.proxmox.host
            url = f"https://{host}:8006/?console=kvm&novnc=1&vmid={vmid}&node={node}&port={port}"

            # Launch system browser
            if sys.platform == "win32":
                subprocess.run(["start", url], shell=True)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", url])
            else:  # Linux
                subprocess.run(["xdg-open", url])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open external VNC: {e}")
