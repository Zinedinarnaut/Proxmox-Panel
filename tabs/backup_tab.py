# proxmox_manager/tabs/backup_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QListWidget, QMessageBox

class BackupTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.vm_id_input = QLineEdit()
        self.vm_id_input.setPlaceholderText("VMID")
        layout.addWidget(self.vm_id_input)

        btn_layout = QHBoxLayout()
        self.create_backup_btn = QPushButton("Create Backup")
        self.create_backup_btn.clicked.connect(self.create_backup)
        btn_layout.addWidget(self.create_backup_btn)

        self.restore_backup_btn = QPushButton("Restore Backup")
        self.restore_backup_btn.clicked.connect(self.restore_backup)
        btn_layout.addWidget(self.restore_backup_btn)

        layout.addLayout(btn_layout)

        self.backup_list = QListWidget()
        layout.addWidget(self.backup_list)

        self.refresh_btn = QPushButton("Refresh Backups")
        self.refresh_btn.clicked.connect(self.refresh_backup_list)
        layout.addWidget(self.refresh_btn)

    def create_backup(self):
        vmid_str = self.vm_id_input.text().strip()
        if not vmid_str.isdigit():
            return
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            return
        try:
            self.proxmox.nodes(node).vzdump.post(
                vmid=vmid,
                storage="local",
                mode="snapshot",
                compress="lz4",
                dumpdir="/var/lib/vz/dump"
            )
            QMessageBox.information(self, "Backup", f"Backup job started for VM {vmid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup: {e}")

    def refresh_backup_list(self):
        self.backup_list.clear()
        node = "pve"
        storage = "local"
        try:
            content = self.proxmox.nodes(node).storage(storage).content.get()
            for item in content:
                if item.get('content') == 'backup':
                    volid = item.get('volid', '')
                    vm_in_backup = item.get('vmid', '')
                    self.backup_list.addItem(f"{volid} ({vm_in_backup})")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list backups: {e}")

    def restore_backup(self):
        sel_item = self.backup_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select a backup.")
            return
        line = sel_item.text()
        # e.g. "local:backup/vzdump-qemu-101-2023_01_01-00_00_00.vma.lzo (101)"
        try:
            volid = line.split(" (")[0]
            vmid_in_backup = line.split("(")[1].split(")")[0]
            from PyQt6.QtWidgets import QInputDialog
            new_vmid_str, ok = QInputDialog.getText(self, "Restore Backup", "Enter target VMID:")
            if not ok or not new_vmid_str.isdigit():
                return
            new_vmid = int(new_vmid_str)
            node = "pve"
            self.proxmox.nodes(node).storage("local").restore.post(
                vmid=new_vmid,
                volid=volid,
                storage="local"
            )
            QMessageBox.information(self, "Restored", f"Restore job started for backup {volid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore backup: {e}")

    def find_vm_node(self, vmid):
        # naive approach
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                qemus = self.proxmox.nodes(node_name).qemu.get()
                for vm in qemus:
                    if vm['vmid'] == vmid:
                        return node_name
        except:
            pass
        return None
