# proxmox_manager/tabs/user_mgmt_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QMessageBox, QLineEdit, QLabel
)

class UserMgmtTab(QWidget):
    """
    Demonstrates listing, creating, and removing Proxmox users.
    For advanced usage, you can expand on role assignments, password resets, etc.
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("User Management")
        layout.addWidget(title_label)

        # List of users
        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        # Buttons row
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Users")
        self.refresh_btn.clicked.connect(self.refresh_users)
        btn_layout.addWidget(self.refresh_btn)

        self.remove_btn = QPushButton("Remove Selected User")
        self.remove_btn.clicked.connect(self.remove_user)
        btn_layout.addWidget(self.remove_btn)

        layout.addLayout(btn_layout)

        # Form to create user
        create_layout = QHBoxLayout()
        self.new_user_input = QLineEdit()
        self.new_user_input.setPlaceholderText("User ID (e.g., jdoe@pam)")
        create_layout.addWidget(self.new_user_input)

        self.new_user_pass = QLineEdit()
        self.new_user_pass.setPlaceholderText("Password")
        self.new_user_pass.setEchoMode(QLineEdit.EchoMode.Password)  # hide typed chars
        create_layout.addWidget(self.new_user_pass)

        self.create_btn = QPushButton("Create User")
        self.create_btn.clicked.connect(self.create_user)
        create_layout.addWidget(self.create_btn)

        layout.addLayout(create_layout)

        self.setLayout(layout)

    def refresh_users(self):
        """
        GET /access/users
        This returns a list of user objects with fields like 'userid', 'comment', etc.
        """
        self.user_list.clear()
        try:
            users = self.proxmox.access.users.get()
            for u in users:
                userid = u.get('userid', '')
                comment = u.get('comment', '')
                # Might also have 'expire', 'enable', 'realm', etc.
                display = f"{userid} - {comment}"
                self.user_list.addItem(display)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list users: {e}")

    def create_user(self):
        """
        POST /access/users
        fields: userid=..., password=..., realm=? (pam?), comment=...
        """
        userid = self.new_user_input.text().strip()
        password = self.new_user_pass.text().strip()
        if not userid or not password:
            QMessageBox.warning(self, "Warning", "User ID or password is empty.")
            return
        try:
            self.proxmox.access.users.post(userid=userid, password=password)
            QMessageBox.information(self, "Created", f"User {userid} created.")
            # Clear input fields
            self.new_user_input.clear()
            self.new_user_pass.clear()
            self.refresh_users()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create user {userid}: {e}")

    def remove_user(self):
        """
        DELETE /access/users/{userid}
        parse from selected item
        """
        item = self.user_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a user.")
            return
        line = item.text()  # e.g. "jdoe@pam - John Doe"
        userid = line.split(" - ")[0].strip()
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove user {userid}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # e.g. 'jdoe@pam'
                self.proxmox.access.users(userid).delete()
                QMessageBox.information(self, "Removed", f"User {userid} removed.")
                self.refresh_users()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove user: {e}")
