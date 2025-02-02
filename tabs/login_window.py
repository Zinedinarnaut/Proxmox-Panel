# proxmox_manager/login_window.py

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from proxmoxer import ProxmoxAPI

class LoginWindow(QWidget):
    """
    A simple login form for Proxmox:
    - Host (IP or domain)
    - Username (e.g. root@pam)
    - Password
    - Optional: token-based login or a realm field
    Once verified, it calls self.on_login_success(proxmox).
    """
    def __init__(self, on_login_success):
        """
        :param on_login_success: a callback function that receives 'proxmox' when login is successful
        """
        super().__init__()
        self.setWindowTitle("Proxmox Login")
        self.on_login_success = on_login_success
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.host_label = QLabel("Host (IP or domain):")
        layout.addWidget(self.host_label)
        self.host_input = QLineEdit()
        self.host_input.setText("192.168.0.21")  # default or blank
        layout.addWidget(self.host_input)

        self.user_label = QLabel("Username (e.g. root@pam):")
        layout.addWidget(self.user_label)
        self.user_input = QLineEdit()
        self.user_input.setText("root@pam")
        layout.addWidget(self.user_input)

        self.password_label = QLabel("Password:")
        layout.addWidget(self.password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setText("1234")  # default or blank
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

    def handle_login(self):
        host = self.host_input.text().strip()
        user = self.user_input.text().strip()
        passwd = self.password_input.text()  # allow blank?

        if not host or not user:
            QMessageBox.warning(self, "Warning", "Please enter a host and username.")
            return

        # Attempt to connect
        try:
            proxmox = ProxmoxAPI(
                host,
                user=user,
                password=passwd,
                verify_ssl=False  # or True if you have a valid cert
            )
            # Optionally do a quick test, e.g.:
            _ = proxmox.version.get()  # test a simple endpoint

            # If successful, call the callback
            self.on_login_success(proxmox)

        except Exception as e:
            QMessageBox.critical(self, "Login Failed", f"Error: {e}")
