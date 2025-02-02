# proxmox_manager/tabs/firewall_options_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QMessageBox
)

class FirewallOptionsTab(QWidget):
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

        self.load_btn = QPushButton("Load Options")
        self.load_btn.clicked.connect(self.load_options)
        node_layout.addWidget(self.load_btn)
        layout.addLayout(node_layout)

        # Loglevel
        loglevel_layout = QHBoxLayout()
        loglevel_label = QLabel("Log Level:")
        loglevel_layout.addWidget(loglevel_label)
        self.loglevel_combo = QComboBox()
        self.loglevel_combo.addItems(["info", "debug", "err", "nolog"])  # example
        loglevel_layout.addWidget(self.loglevel_combo)
        layout.addLayout(loglevel_layout)

        # nf_conntrack
        self.nf_conntrack_cb = QCheckBox("nf_conntrack")
        layout.addWidget(self.nf_conntrack_cb)

        # nosmurfs
        self.nosmurfs_cb = QCheckBox("No Smurfs")
        layout.addWidget(self.nosmurfs_cb)

        # tcpflags_log
        self.tcpflags_log_cb = QCheckBox("TCP Flags Log")
        layout.addWidget(self.tcpflags_log_cb)

        # Save button
        self.save_btn = QPushButton("Save Options")
        self.save_btn.clicked.connect(self.save_options)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)

    def load_options(self):
        """
        GET /nodes/{node}/firewall/options
        """
        node = self.node_combo.currentText()
        try:
            opts = self.proxmox.nodes(node).firewall.options.get()
            # 'opts' might include fields like loglevel, nf_conntrack, nosmurfs, tcpflags_log
            loglevel = opts.get('loglevel', 'info')
            self.loglevel_combo.setCurrentText(loglevel)

            nf_conntrack = opts.get('nf_conntrack', 1)
            self.nf_conntrack_cb.setChecked(bool(nf_conntrack))

            nosmurfs = opts.get('nosmurfs', 0)
            self.nosmurfs_cb.setChecked(bool(nosmurfs))

            tcpflags_log = opts.get('tcpflags_log', 0)
            self.tcpflags_log_cb.setChecked(bool(tcpflags_log))

            QMessageBox.information(self, "Loaded", "Firewall options loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load firewall options: {e}")

    def save_options(self):
        """
        PUT /nodes/{node}/firewall/options
        For example: { loglevel=..., nf_conntrack=..., nosmurfs=..., tcpflags_log=... }
        """
        node = self.node_combo.currentText()
        data = {
            "loglevel": self.loglevel_combo.currentText(),
            "nf_conntrack": int(self.nf_conntrack_cb.isChecked()),
            "nosmurfs": int(self.nosmurfs_cb.isChecked()),
            "tcpflags_log": int(self.tcpflags_log_cb.isChecked())
        }
        try:
            self.proxmox.nodes(node).firewall.options.put(**data)
            QMessageBox.information(self, "Saved", "Firewall options saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save options: {e}")
