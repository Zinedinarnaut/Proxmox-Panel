# proxmox_manager/tabs/logs_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QLineEdit, QPushButton, QMessageBox

class LogsTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.current_logs = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.logs_display = QTextEdit()
        self.logs_display.setReadOnly(True)
        layout.addWidget(self.logs_display)

        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter logs")
        filter_layout.addWidget(self.filter_input)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.clicked.connect(self.filter_logs)
        filter_layout.addWidget(self.filter_btn)

        layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Logs")
        self.refresh_btn.clicked.connect(self.refresh_logs)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_logs(self):
        self.current_logs = []
        self.logs_display.clear()
        try:
            logs = self.proxmox.cluster.log.get()
            self.current_logs = logs
            self.display_logs(logs)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh logs: {e}")

    def display_logs(self, logs):
        self.logs_display.clear()
        for entry in logs:
            msg = entry.get('msg', '')
            node = entry.get('node', '')
            user = entry.get('user', '')
            self.logs_display.append(f"[{node}] {user}: {msg}")

    def filter_logs(self):
        query = self.filter_input.text().lower()
        filtered = []
        for entry in self.current_logs:
            combined = str(entry).lower()
            if query in combined:
                filtered.append(entry)
        self.display_logs(filtered)
