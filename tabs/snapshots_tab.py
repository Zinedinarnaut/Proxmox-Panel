# proxmox_manager/tabs/snapshots_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QListWidget, QMessageBox

class SnapshotsTab(QWidget):
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
        self.list_btn = QPushButton("List Snapshots")
        self.list_btn.clicked.connect(self.list_snapshots)
        btn_layout.addWidget(self.list_btn)

        self.create_btn = QPushButton("Create Snapshot")
        self.create_btn.clicked.connect(self.create_snapshot)
        btn_layout.addWidget(self.create_btn)

        self.restore_btn = QPushButton("Restore Snapshot")
        self.restore_btn.clicked.connect(self.restore_snapshot)
        btn_layout.addWidget(self.restore_btn)

        self.delete_btn = QPushButton("Delete Snapshot")
        self.delete_btn.clicked.connect(self.delete_snapshot)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        self.snapshot_list = QListWidget()
        layout.addWidget(self.snapshot_list)
        self.setLayout(layout)

    def list_snapshots(self):
        self.snapshot_list.clear()
        vmid_str = self.vm_id_input.text().strip()
        if not vmid_str.isdigit():
            QMessageBox.warning(self, "Warning", "Enter a valid VMID.")
            return
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            QMessageBox.warning(self, "Warning", f"No node found for VMID {vmid}.")
            return
        try:
            snaps = self.proxmox.nodes(node).qemu(vmid).snapshot.get()
            for snap in snaps:
                self.snapshot_list.addItem(snap['name'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list snapshots: {e}")

    def create_snapshot(self):
        vmid_str = self.vm_id_input.text().strip()
        if not vmid_str.isdigit():
            return
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            return
        from PyQt6.QtWidgets import QInputDialog
        snap_name, ok = QInputDialog.getText(self, "Create Snapshot", "Snapshot name:")
        if not ok or not snap_name:
            return
        try:
            self.proxmox.nodes(node).qemu(vmid).snapshot.post(snapname=snap_name)
            QMessageBox.information(self, "Created", f"Created snapshot {snap_name}")
            self.list_snapshots()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create snapshot: {e}")

    def restore_snapshot(self):
        item = self.snapshot_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a snapshot.")
            return
        snap_name = item.text()
        vmid_str = self.vm_id_input.text().strip()
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            return
        confirm = QMessageBox.question(
            self,
            "Restore",
            f"Restore snapshot {snap_name} for VM {vmid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.nodes(node).qemu(vmid).snapshot(snap_name).rollback.post()
                QMessageBox.information(self, "Restored", f"Snapshot {snap_name} restored.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to restore snapshot: {e}")

    def delete_snapshot(self):
        item = self.snapshot_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a snapshot.")
            return
        snap_name = item.text()
        vmid_str = self.vm_id_input.text().strip()
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            return
        confirm = QMessageBox.question(
            self,
            "Delete",
            f"Delete snapshot {snap_name} for VM {vmid}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.nodes(node).qemu(vmid).snapshot(snap_name).delete()
                QMessageBox.information(self, "Deleted", f"Snapshot {snap_name} deleted.")
                self.list_snapshots()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete snapshot: {e}")

    def find_vm_node(self, vmid):
        # naive search for the node that hosts vmid
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                qemus = self.proxmox.nodes(node_name).qemu.get()
                for vm in qemus:
                    if vm['vmid'] == vmid:
                        return node_name
        except:
            return None
        return None
