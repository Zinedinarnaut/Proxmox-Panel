# proxmox_manager/tabs/firewall_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QLineEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt

class FirewallTab(QWidget):
    """
    A demonstration for node-level firewall management.
    Lists the rules, allows adding/removing rules, toggling the firewall on or off.
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        # We pick one "node" to manage firewall, or let the user select.
        # For a multi-node environment, you can do a node selection combo in the UI.
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Node selection (in case multiple nodes)
        node_layout = QHBoxLayout()
        node_label = QLabel("Node:")
        node_layout.addWidget(node_label)

        self.node_combo = QComboBox()
        try:
            nodes = self.proxmox.nodes.get()
            for n in nodes:
                self.node_combo.addItem(n['node'])
        except:
            self.node_combo.addItem("pve")  # fallback
        node_layout.addWidget(self.node_combo)

        self.refresh_rules_btn = QPushButton("Refresh Rules")
        self.refresh_rules_btn.clicked.connect(self.refresh_rules)
        node_layout.addWidget(self.refresh_rules_btn)
        layout.addLayout(node_layout)

        # Firewall enable/disable
        fw_btn_layout = QHBoxLayout()
        self.enable_fw_btn = QPushButton("Enable Firewall")
        self.enable_fw_btn.clicked.connect(self.enable_firewall)
        fw_btn_layout.addWidget(self.enable_fw_btn)

        self.disable_fw_btn = QPushButton("Disable Firewall")
        self.disable_fw_btn.clicked.connect(self.disable_firewall)
        fw_btn_layout.addWidget(self.disable_fw_btn)
        layout.addLayout(fw_btn_layout)

        # List of rules
        self.rules_list = QListWidget()
        layout.addWidget(self.rules_list)

        # Add rule area
        rule_form_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["in", "out"])  # direction
        rule_form_layout.addWidget(self.type_combo)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["ACCEPT", "DROP", "REJECT"])
        rule_form_layout.addWidget(self.action_combo)

        self.proto_input = QLineEdit()
        self.proto_input.setPlaceholderText("Protocol (tcp/udp/icmp?)")
        rule_form_layout.addWidget(self.proto_input)

        self.dest_port_input = QLineEdit()
        self.dest_port_input.setPlaceholderText("Dest port (e.g. 22)")
        rule_form_layout.addWidget(self.dest_port_input)

        self.add_rule_btn = QPushButton("Add Rule")
        self.add_rule_btn.clicked.connect(self.add_rule)
        rule_form_layout.addWidget(self.add_rule_btn)

        layout.addLayout(rule_form_layout)

        # Remove rule button
        self.remove_rule_btn = QPushButton("Remove Selected Rule")
        self.remove_rule_btn.clicked.connect(self.remove_rule)
        layout.addWidget(self.remove_rule_btn)

    def refresh_rules(self):
        """
        GET /api2/json/nodes/{node}/firewall/rules
        """
        self.rules_list.clear()
        node = self.node_combo.currentText()
        try:
            rules = self.proxmox.nodes(node).firewall.rules.get()
            # Each rule has an index or pos. We'll store that in item data.
            for r in rules:
                pos = r.get('pos', '')
                action = r.get('action', '')
                direction = r.get('type', '')  # 'in'/'out'
                proto = r.get('proto', '')
                dport = r.get('dport', '')
                enable = r.get('enable', 1)
                display = f"{pos}: {direction} {action} proto={proto} dport={dport}, enable={enable}"
                item = f"{display}"
                # You might store the rule object or pos in item data for reference
                self.rules_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list firewall rules: {e}")

    def add_rule(self):
        """
        POST /api2/json/nodes/{node}/firewall/rules
        fields: type=..., action=..., proto=..., dport=...
        """
        node = self.node_combo.currentText()
        direction = self.type_combo.currentText()
        action = self.action_combo.currentText()
        proto = self.proto_input.text().strip() or "tcp"
        dport = self.dest_port_input.text().strip()
        if not dport:
            QMessageBox.warning(self, "Warning", "Please specify a dest port.")
            return
        try:
            self.proxmox.nodes(node).firewall.rules.post(
                type=direction,
                action=action,
                proto=proto,
                dport=dport,
                enable=1  # default to enabled
            )
            QMessageBox.information(self, "Success", "Rule added.")
            self.refresh_rules()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add rule: {e}")

    def remove_rule(self):
        """
        DELETE /api2/json/nodes/{node}/firewall/rules/{pos}
        We need to parse the 'pos' from the selected item text.
        """
        node = self.node_combo.currentText()
        sel_item = self.rules_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select a rule first.")
            return
        text = sel_item.text()  # e.g. "0: in ACCEPT proto=tcp dport=22..."
        pos_str = text.split(":")[0]
        pos_str = pos_str.strip()
        try:
            self.proxmox.nodes(node).firewall.rules(pos_str).delete()
            QMessageBox.information(self, "Removed", f"Removed rule at pos={pos_str}")
            self.refresh_rules()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove rule: {e}")

    def enable_firewall(self):
        """
        PUT /api2/json/nodes/{node}/firewall/options
        { enable: 1 }
        """
        node = self.node_combo.currentText()
        try:
            self.proxmox.nodes(node).firewall.options.put(enable=1)
            QMessageBox.information(self, "Enabled", "Firewall enabled.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to enable firewall: {e}")

    def disable_firewall(self):
        node = self.node_combo.currentText()
        try:
            self.proxmox.nodes(node).firewall.options.put(enable=0)
            QMessageBox.information(self, "Disabled", "Firewall disabled.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to disable firewall: {e}")
