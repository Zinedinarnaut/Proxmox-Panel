# proxmox_manager/tabs/lxc_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QMessageBox

class LXCTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.lxc_list = QListWidget()
        layout.addWidget(self.lxc_list)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh LXC")
        self.refresh_btn.clicked.connect(self.refresh_lxc_list)
        btn_layout.addWidget(self.refresh_btn)

        self.create_btn = QPushButton("Create LXC")
        self.create_btn.clicked.connect(self.create_lxc)
        btn_layout.addWidget(self.create_btn)

        self.remove_btn = QPushButton("Remove LXC")
        self.remove_btn.clicked.connect(self.remove_lxc)
        btn_layout.addWidget(self.remove_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_lxc_list(self):
        self.lxc_list.clear()
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                lxcs = self.proxmox.nodes(node_name).lxc.get()
                for lxc in lxcs:
                    vmid = lxc['vmid']
                    name = lxc.get('name', 'N/A')
                    status = lxc.get('status', 'unknown')
                    self.lxc_list.addItem(f"{name} (CT {vmid}) - {status} on {node_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list LXCs: {e}")

    def create_lxc(self):
        from PyQt6.QtWidgets import QInputDialog
        node, ok = QInputDialog.getText(self, "Create LXC", "Which node?")
        if not ok or not node:
            return
        ct_id_str, ok2 = QInputDialog.getText(self, "Create LXC", "Enter new CT ID:")
        if not ok2 or not ct_id_str.isdigit():
            return
        ct_id = int(ct_id_str)
        try:
            # Minimal example
            self.proxmox.nodes(node).lxc.post(
                vmid=ct_id,
                hostname=f"lxc-{ct_id}",
                ostemplate="local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz",
                storage="local-lvm",
                memory=512,
                cores=1
            )
            QMessageBox.information(self, "Created", f"Created LXC {ct_id}")
            self.refresh_lxc_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create LXC: {e}")

    def remove_lxc(self):
        sel = self.lxc_list.currentItem()
        if not sel:
            QMessageBox.warning(self, "Warning", "Select an LXC.")
            return
        line = sel.text()
        # e.g. "myLXC (CT 105) - running on pve"
        try:
            ct_id = line.split("(CT ")[1].split(")")[0].strip()
            node = line.split(" on ")[-1]
            confirm = QMessageBox.question(
                self, "Confirm", f"Remove LXC {ct_id} on {node}? Cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.proxmox.nodes(node).lxc(ct_id).delete()
                QMessageBox.information(self, "Removed", f"Removed LXC {ct_id}")
                self.refresh_lxc_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove LXC: {e}")
