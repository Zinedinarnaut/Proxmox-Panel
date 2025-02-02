# proxmox_manager/tabs/task_log_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt6.QtCore import Qt

class TaskLogTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.current_tasks = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter tasks by VMID/User/Etc.")
        filter_layout.addWidget(self.filter_input)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.clicked.connect(self.filter_tasks)
        filter_layout.addWidget(self.filter_btn)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["UPID", "Type", "User", "VMID", "Status"])
        layout.addWidget(self.table)

        self.refresh_btn = QPushButton("Refresh Tasks")
        self.refresh_btn.clicked.connect(self.refresh_tasks)
        layout.addWidget(self.refresh_btn)

        self.setLayout(layout)

    def refresh_tasks(self):
        self.current_tasks = []
        self.table.setRowCount(0)
        try:
            # proxmox.cluster.tasks.get() might return a big list
            tasks = self.proxmox.cluster.tasks.get()
            self.current_tasks = tasks
            self.display_tasks(tasks)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch tasks: {e}")

    def display_tasks(self, tasks):
        self.table.setRowCount(0)
        for t in tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            upid = t.get('upid', '')
            ttype = t.get('type', '')
            user = t.get('user', '')
            vmid = t.get('vmid', '')
            status = t.get('status', '')

            self.table.setItem(row, 0, QTableWidgetItem(upid))
            self.table.setItem(row, 1, QTableWidgetItem(ttype))
            self.table.setItem(row, 2, QTableWidgetItem(user))
            self.table.setItem(row, 3, QTableWidgetItem(str(vmid)))
            self.table.setItem(row, 4, QTableWidgetItem(status))

    def filter_tasks(self):
        query = self.filter_input.text().lower()
        filtered = []
        for t in self.current_tasks:
            combined = str(t).lower()
            if query in combined:
                filtered.append(t)
        self.display_tasks(filtered)
