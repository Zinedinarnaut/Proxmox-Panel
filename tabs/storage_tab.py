# proxmox_manager/tabs/storage_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QPushButton, QFileDialog, QMessageBox

class StorageTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        storage_label = QLabel("Storage Management")
        layout.addWidget(storage_label)

        self.storage_list = QListWidget()
        layout.addWidget(self.storage_list)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Storage")
        self.refresh_btn.clicked.connect(self.refresh_storage_list)
        btn_layout.addWidget(self.refresh_btn)

        self.upload_iso_btn = QPushButton("Upload ISO")
        self.upload_iso_btn.clicked.connect(self.upload_iso)
        btn_layout.addWidget(self.upload_iso_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_storage_list(self):
        self.storage_list.clear()
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                storages = self.proxmox.nodes(node_name).storage.get()
                for st in storages:
                    text = f"Node: {node_name}, Storage: {st.get('storage')}, Type: {st.get('type')}"
                    self.storage_list.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list storages: {e}")

    def upload_iso(self):
        node = "pve"
        file_dialog = QFileDialog(self, "Select ISO to upload")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path.lower().endswith(".iso"):
                QMessageBox.warning(self, "Warning", "Please select an ISO file.")
                return
            storages = self.proxmox.nodes(node).storage.get()
            iso_storage = None
            for st in storages:
                if 'content' in st and 'iso' in st['content'].split(","):
                    iso_storage = st['storage']
                    break
            if not iso_storage:
                QMessageBox.critical(self, "Error", "No storage found that can store ISO.")
                return
            try:
                with open(file_path, 'rb') as iso_file:
                    self.proxmox.nodes(node).storage(iso_storage).upload.post(
                        content='iso',
                        filename=file_path.split('/')[-1],
                        file=iso_file
                    )
                QMessageBox.information(self, "Success", f"Uploaded {file_path} to {iso_storage}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload ISO: {e}")
