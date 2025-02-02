# proxmox_manager/tabs/network_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QHBoxLayout, QPushButton, QMessageBox

class NetworkTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Network Management")
        layout.addWidget(label)

        self.network_list = QListWidget()
        layout.addWidget(self.network_list)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Network")
        self.refresh_btn.clicked.connect(self.refresh_network_list)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def refresh_network_list(self):
        self.network_list.clear()
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                nets = self.proxmox.nodes(node_name).network.get()
                for net in nets:
                    iface = net.get('iface', 'unknown')
                    net_type = net.get('type', 'unknown')
                    ports = net.get('bridge_ports', '')
                    text = f"Node: {node_name}, IF: {iface}, Type: {net_type}, Ports: {ports}"
                    self.network_list.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list networks: {e}")
