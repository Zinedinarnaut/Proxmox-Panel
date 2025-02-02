# proxmox_manager/tabs/replication_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

class ReplicationTab(QWidget):
    """
    Manage VM Replication tasks (schedules that replicate a VM from one node/storage to another).
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Replications")
        self.refresh_btn.clicked.connect(self.refresh_replications)
        top_layout.addWidget(self.refresh_btn)

        self.create_btn = QPushButton("Create Replication")
        self.create_btn.clicked.connect(self.create_replication)
        top_layout.addWidget(self.create_btn)
        layout.addLayout(top_layout)

        self.replication_list = QListWidget()
        layout.addWidget(self.replication_list)

        remove_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected Replication")
        self.remove_btn.clicked.connect(self.remove_replication)
        remove_layout.addWidget(self.remove_btn)
        layout.addLayout(remove_layout)

        # A minimal form to set up replication
        form_layout = QHBoxLayout()
        self.vmid_input = QLineEdit()
        self.vmid_input.setPlaceholderText("VMID to replicate")
        form_layout.addWidget(self.vmid_input)

        self.target_node_combo = QComboBox()
        form_layout.addWidget(self.target_node_combo)
        # Populate with node list
        try:
            nodes = self.proxmox.nodes.get()
            for n in nodes:
                self.target_node_combo.addItem(n['node'])
        except:
            pass

        self.schedule_input = QLineEdit()
        self.schedule_input.setPlaceholderText("Schedule (e.g. every 1h, crontab...)")
        form_layout.addWidget(self.schedule_input)

        layout.addLayout(form_layout)

        self.setLayout(layout)

    def refresh_replications(self):
        """
        GET /cluster/replication
        Returns a list of replication jobs for the cluster.
        """
        self.replication_list.clear()
        try:
            result = self.proxmox.cluster.replication.get()
            # each job has 'id', 'jobid', 'node', 'target', 'schedule', etc.
            for job in result:
                jobid = job.get('jobid', '')  # typically "vmid-id" or so
                node = job.get('node', '')
                target = job.get('target', '')
                schedule = job.get('schedule', '')
                display = f"{jobid} on {node} -> {target}, schedule={schedule}"
                self.replication_list.addItem(display)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list replications: {e}")

    def create_replication(self):
        """
        POST /cluster/replication
        fields:
          - node (source node)
          - target (target node)
          - vmid
          - schedule
          - type='local' (usually)
          - etc.
        """
        vmid_str = self.vmid_input.text().strip()
        if not vmid_str.isdigit():
            QMessageBox.warning(self, "Warning", "Enter a valid VMID.")
            return
        vmid = int(vmid_str)
        target_node = self.target_node_combo.currentText()
        schedule = self.schedule_input.text().strip() or "*/30"  # default every 30min?

        # We also need a "source node." We'll guess the node from find_vm_node or user input
        source_node = self.find_vm_node(vmid)
        if not source_node:
            QMessageBox.warning(self, "Warning", f"Cannot find node hosting VM {vmid}.")
            return

        try:
            data = {
                "node": source_node,
                "target": target_node,
                "vmid": vmid,
                "schedule": schedule
            }
            self.proxmox.cluster.replication.post(**data)
            QMessageBox.information(self, "Created", "Replication job created.")
            self.refresh_replications()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create replication: {e}")

    def remove_replication(self):
        """
        We parse jobid from the selected list item and do:
        DELETE /cluster/replication/{jobid}
        """
        sel_item = self.replication_list.currentItem()
        if not sel_item:
            QMessageBox.warning(self, "Warning", "Select a replication job.")
            return
        line = sel_item.text()  # e.g. "100-0 on pve -> pve2, schedule=every 1h"
        jobid = line.split(" ")[0]  # "100-0"
        try:
            self.proxmox.cluster.replication(jobid).delete()
            QMessageBox.information(self, "Removed", f"Removed replication job {jobid}")
            self.refresh_replications()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove replication: {e}")

    def find_vm_node(self, vmid):
        """Similar logic to snapshots. We search which node has that VM."""
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
