# proxmox_manager/tabs/ha_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QMessageBox

class HATab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.ha_list = QListWidget()
        layout.addWidget(self.ha_list)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh HA")
        self.refresh_btn.clicked.connect(self.refresh_ha)
        btn_layout.addWidget(self.refresh_btn)

        # Example: place a "Set Maintenance" or "Unset Maintenance" button
        self.maint_btn = QPushButton("Toggle Maintenance")
        self.maint_btn.clicked.connect(self.toggle_maintenance)
        btn_layout.addWidget(self.maint_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_ha(self):
        self.ha_list.clear()
        try:
            # https://pve.proxmox.com/pve-docs/api-viewer/index.html
            # For example: /cluster/ha/resources
            resources = self.proxmox.cluster.ha.resources.get()
            for r in resources:
                sid = r.get('sid', 'N/A')
                state = r.get('state', 'N/A')
                self.ha_list.addItem(f"{sid} - state={state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list HA resources: {e}")

    def toggle_maintenance(self):
        """Naive example: if the first selected resource is 'started', set it to maintenance, or vice versa."""
        item = self.ha_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select an HA resource.")
            return
        text = item.text()  # e.g. "vm:101 - state=started"
        sid = text.split(" ")[0].strip()  # "vm:101"
        # fetch state
        state_str = text.split("=")[-1]
        newstate = "maintenance" if "started" in state_str else "started"
        try:
            # proxmox.cluster.ha.resources(sid).post(state=newstate)
            self.proxmox.cluster.ha.resources(sid).post(state=newstate)
            QMessageBox.information(self, "Success", f"Set {sid} to {newstate}")
            self.refresh_ha()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set state: {e}")
