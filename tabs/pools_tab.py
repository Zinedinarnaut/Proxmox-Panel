# proxmox_manager/tabs/pools_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QMessageBox
)

class PoolsTab(QWidget):
    """
    Manage Proxmox Pools: create new pools, list them, add VMs, remove VMs, etc.
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Pools")
        self.refresh_btn.clicked.connect(self.refresh_pools)
        top_layout.addWidget(self.refresh_btn)

        self.create_pool_btn = QPushButton("Create Pool")
        self.create_pool_btn.clicked.connect(self.create_pool)
        top_layout.addWidget(self.create_pool_btn)

        layout.addLayout(top_layout)

        self.pools_list = QListWidget()
        layout.addWidget(self.pools_list)

        remove_layout = QHBoxLayout()
        self.remove_pool_btn = QPushButton("Remove Selected Pool")
        self.remove_pool_btn.clicked.connect(self.remove_pool)
        remove_layout.addWidget(self.remove_pool_btn)
        layout.addLayout(remove_layout)

        # Minimal form to add a VM to a pool
        add_vm_layout = QHBoxLayout()
        self.pool_input = QLineEdit()
        self.pool_input.setPlaceholderText("Pool name to modify")
        add_vm_layout.addWidget(self.pool_input)

        self.vmid_input = QLineEdit()
        self.vmid_input.setPlaceholderText("VMID to add or remove")
        add_vm_layout.addWidget(self.vmid_input)

        self.add_vm_btn = QPushButton("Add VM to Pool")
        self.add_vm_btn.clicked.connect(self.add_vm_to_pool)
        add_vm_layout.addWidget(self.add_vm_btn)

        self.remove_vm_btn = QPushButton("Remove VM from Pool")
        self.remove_vm_btn.clicked.connect(self.remove_vm_from_pool)
        add_vm_layout.addWidget(self.remove_vm_btn)

        layout.addLayout(add_vm_layout)

        self.setLayout(layout)

    def refresh_pools(self):
        """
        GET /pools
        """
        self.pools_list.clear()
        try:
            pools = self.proxmox.pools.get()
            # each pool has a 'poolid', 'comment', 'members'
            for p in pools:
                pid = p.get('poolid', '')
                comment = p.get('comment', '')
                members = p.get('members', [])
                display = f"{pid} - {comment}, {len(members)} members"
                self.pools_list.addItem(display)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list pools: {e}")

    def create_pool(self):
        """
        POST /pools
        fields: poolid=..., comment=...
        """
        name = self.pool_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Pool name is empty.")
            return
        try:
            self.proxmox.pools.post(poolid=name)
            QMessageBox.information(self, "Created", f"Created pool {name}")
            self.refresh_pools()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create pool: {e}")

    def remove_pool(self):
        """
        DELETE /pools/{poolid}
        parse from selected item
        """
        item = self.pools_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a pool.")
            return
        line = item.text()  # e.g. "my-pool - my test comment, 3 members"
        poolid = line.split(" - ")[0].strip()
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove pool {poolid}? All references removed but VMs remain ungrouped.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.pools(poolid).delete()
                QMessageBox.information(self, "Removed", f"Removed pool {poolid}")
                self.refresh_pools()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove pool: {e}")

    def add_vm_to_pool(self):
        """
        POST /pools/{poolid}
        fields: vmid=..., type='qemu'
        For containers: type='lxc'
        """
        poolid = self.pool_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not (poolid and vmid_str.isdigit()):
            QMessageBox.warning(self, "Warning", "Pool name or VMID invalid.")
            return
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            QMessageBox.warning(self, "Warning", f"Cannot find node for VM {vmid}")
            return
        # We guess it's a QEMU VM. For containers, you'd do type='lxc'
        try:
            self.proxmox.pools(poolid).post(vmid=vmid, node=node, type='qemu')
            QMessageBox.information(self, "Added", f"VM {vmid} to pool {poolid}")
            self.refresh_pools()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add VM to pool: {e}")

    def remove_vm_from_pool(self):
        """
        DELETE /pools/{poolid}
        fields: vmid=..., node=..., type=...
        """
        poolid = self.pool_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not (poolid and vmid_str.isdigit()):
            QMessageBox.warning(self, "Warning", "Pool name or VMID invalid.")
            return
        vmid = int(vmid_str)
        node = self.find_vm_node(vmid)
        if not node:
            QMessageBox.warning(self, "Warning", f"Cannot find node for VM {vmid}")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove VM {vmid} from pool {poolid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.pools(poolid).delete(
                    vmid=vmid, node=node, type='qemu'
                )
                QMessageBox.information(self, "Removed", f"Removed VM {vmid} from pool {poolid}")
                self.refresh_pools()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove VM from pool: {e}")

    def find_vm_node(self, vmid):
        """
        As done in snapshots or replication code, we find which node has a QEMU VM matching vmid.
        """
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    if vm['vmid'] == vmid:
                        return node_name
        except:
            pass
        return None
