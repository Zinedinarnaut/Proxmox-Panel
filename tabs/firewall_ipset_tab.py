# proxmox_manager/tabs/firewall_ipset_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QLabel, QLineEdit, QMessageBox, QComboBox
)

class FirewallIPSetTab(QWidget):
    """
    Demonstrates node-level firewall IPSet management.
    (Analogous logic applies for cluster-level or VM-level sets.)
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Node selection
        node_layout = QHBoxLayout()
        node_label = QLabel("Node:")
        node_layout.addWidget(node_label)

        self.node_combo = QComboBox()
        try:
            nodes = self.proxmox.nodes.get()
            for n in nodes:
                self.node_combo.addItem(n['node'])
        except:
            self.node_combo.addItem("pve")
        node_layout.addWidget(self.node_combo)

        self.refresh_btn = QPushButton("Refresh IPSet List")
        self.refresh_btn.clicked.connect(self.refresh_ipsets)
        node_layout.addWidget(self.refresh_btn)
        layout.addLayout(node_layout)

        # List of IPSets
        self.ipset_list = QListWidget()
        layout.addWidget(self.ipset_list)

        # Create IPSet
        create_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("IPSet Name")
        create_layout.addWidget(self.name_input)

        self.create_btn = QPushButton("Create IPSet")
        self.create_btn.clicked.connect(self.create_ipset)
        create_layout.addWidget(self.create_btn)
        layout.addLayout(create_layout)

        # Remove IPSet
        self.remove_btn = QPushButton("Remove Selected IPSet")
        self.remove_btn.clicked.connect(self.remove_ipset)
        layout.addWidget(self.remove_btn)

        # Manage IP addresses within an IPSet
        manage_label = QLabel("Add/Remove IPs in IPSet:")
        layout.addWidget(manage_label)

        manage_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("CIDR or IP (e.g. 192.168.1.0/24)")
        manage_layout.addWidget(self.ip_input)

        self.add_ip_btn = QPushButton("Add IP")
        self.add_ip_btn.clicked.connect(self.add_ip)
        manage_layout.addWidget(self.add_ip_btn)

        self.remove_ip_btn = QPushButton("Remove IP")
        self.remove_ip_btn.clicked.connect(self.remove_ip)
        manage_layout.addWidget(self.remove_ip_btn)

        layout.addLayout(manage_layout)

        self.setLayout(layout)

    def refresh_ipsets(self):
        """
        GET /nodes/{node}/firewall/ipset
        Lists all IP sets for the node.
        """
        self.ipset_list.clear()
        node = self.node_combo.currentText()
        try:
            ipsets = self.proxmox.nodes(node).firewall.ipset.get()
            # Each ipset has a 'name' and 'comment'
            for s in ipsets:
                name = s.get('name', '')
                comment = s.get('comment', '')
                display = f"{name} - {comment}"
                self.ipset_list.addItem(display)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list IP sets: {e}")

    def create_ipset(self):
        """
        POST /nodes/{node}/firewall/ipset
        fields: name=..., comment=...
        """
        node = self.node_combo.currentText()
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Enter an IPSet name.")
            return
        try:
            self.proxmox.nodes(node).firewall.ipset.post(name=name)
            QMessageBox.information(self, "Success", f"Created IPSet {name}")
            self.refresh_ipsets()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create IPSet: {e}")

    def remove_ipset(self):
        """
        DELETE /nodes/{node}/firewall/ipset/{name}
        """
        node = self.node_combo.currentText()
        sel_item = self.ipset_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select an IPSet.")
            return
        # e.g. "blocklist - Some comment"
        ipset_name = sel_item.text().split(" - ")[0].strip()
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove IPSet {ipset_name}? All IPs in it will also be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.nodes(node).firewall.ipset(ipset_name).delete()
                QMessageBox.information(self, "Removed", f"Removed IPSet {ipset_name}")
                self.refresh_ipsets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove IPSet: {e}")

    def add_ip(self):
        """
        POST /nodes/{node}/firewall/ipset/{name}
        fields: cidr=..., comment=...
        """
        node = self.node_combo.currentText()
        sel_item = self.ipset_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select an IPSet first.")
            return
        ipset_name = sel_item.text().split(" - ")[0].strip()
        cidr = self.ip_input.text().strip()
        if not cidr:
            QMessageBox.warning(self, "Warning", "Enter an IP/CIDR.")
            return
        try:
            self.proxmox.nodes(node).firewall.ipset(ipset_name).post(cidr=cidr)
            QMessageBox.information(self, "Success", f"Added {cidr} to IPSet {ipset_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add IP: {e}")

    def remove_ip(self):
        """
        DELETE /nodes/{node}/firewall/ipset/{name}/{cidr}
        But we do not store the list of IPs. We could parse them by GET ipset name, or ask user?
        """
        node = self.node_combo.currentText()
        sel_item = self.ipset_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select an IPSet first.")
            return
        ipset_name = sel_item.text().split(" - ")[0].strip()
        cidr = self.ip_input.text().strip()
        if not cidr:
            QMessageBox.warning(self, "Warning", "Enter the IP/CIDR to remove.")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove {cidr} from IPSet {ipset_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Note the path: ipset/ipset_name/cidr
                self.proxmox.nodes(node).firewall.ipset(ipset_name)(cidr).delete()
                QMessageBox.information(self, "Removed", f"Removed {cidr} from {ipset_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove IP: {e}")
