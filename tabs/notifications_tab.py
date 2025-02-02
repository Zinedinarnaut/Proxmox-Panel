# proxmox_manager/tabs/notifications_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)

class NotificationsTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.email_address = ""
        self.slack_webhook = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        lbl = QLabel("Notification Settings")
        layout.addWidget(lbl)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Recipient Email Address")
        layout.addWidget(self.email_input)

        self.slack_input = QLineEdit()
        self.slack_input.setPlaceholderText("Slack Webhook URL")
        layout.addWidget(self.slack_input)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)

        self.test_btn = QPushButton("Send Test Notification")
        self.test_btn.clicked.connect(self.test_notification)
        layout.addWidget(self.test_btn)

        self.setLayout(layout)

    def save_settings(self):
        self.email_address = self.email_input.text().strip()
        self.slack_webhook = self.slack_input.text().strip()
        QMessageBox.information(self, "Saved", "Notification settings saved in memory.")

    def test_notification(self):
        """Naive example: Just show a pop-up. Real usage might do an actual email or Slack POST."""
        msg = f"Test notification\nEmail: {self.email_address}\nSlack: {self.slack_webhook}"
        QMessageBox.information(self, "Test Notification", msg)
