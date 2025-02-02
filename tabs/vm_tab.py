# proxmox_manager/tabs/vm_tab.py

import subprocess
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLineEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt

class VmTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Search row
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by VM name/ID")
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_vms)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        # VM list
        self.vm_list = QListWidget()
        self.vm_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.vm_list)

        # Buttons row
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_vms)
        btn_layout.addWidget(self.refresh_btn)

        self.start_btn = QPushButton("Start Selected")
        self.start_btn.clicked.connect(lambda: self.bulk_vm_action("start"))
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Selected")
        self.stop_btn.clicked.connect(lambda: self.bulk_vm_action("stop"))
        btn_layout.addWidget(self.stop_btn)

        self.reset_btn = QPushButton("Reset Selected")
        self.reset_btn.clicked.connect(lambda: self.bulk_vm_action("reset"))
        btn_layout.addWidget(self.reset_btn)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.bulk_remove_vm)
        btn_layout.addWidget(self.remove_btn)

        self.clone_btn = QPushButton("Quick Clone")
        self.clone_btn.clicked.connect(self.quick_clone_vm)
        btn_layout.addWidget(self.clone_btn)

        self.migrate_btn = QPushButton("Migrate")
        self.migrate_btn.clicked.connect(self.migrate_vm)
        btn_layout.addWidget(self.migrate_btn)

        layout.addLayout(btn_layout)

    def refresh_vms(self):
        self.vm_list.clear()
        vms = self.list_vms()
        for node, vmid, name, status in vms:
            self.vm_list.addItem(f"{name} (ID: {vmid}) - {status} on {node}")

    def list_vms(self):
        vm_list = []
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                qemus = self.proxmox.nodes(node_name).qemu.get()
                for vm in qemus:
                    vmid = vm['vmid']
                    name = vm.get('name', 'N/A')
                    status = vm.get('status', 'unknown')
                    vm_list.append((node_name, vmid, name, status))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to list VMs: {e}")
        return vm_list

    def search_vms(self):
        query = self.search_input.text().lower()
        for i in range(self.vm_list.count()):
            item = self.vm_list.item(i)
            text = item.text().lower()
            item.setHidden(query not in text)

    def bulk_vm_action(self, action):
        items = self.vm_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "No VM selected.")
            return
        for item in items:
            self.handle_vm_action(item, action)
        self.refresh_vms()

    def handle_vm_action(self, list_item, action):
        vm_info = list_item.text()
        # e.g. "myVM (ID: 101) - running on pve"
        parts = vm_info.split(" - ")[0].split(" (ID: ")
        vmid = parts[1][:-1]
        node = vm_info.split(" on ")[-1]
        try:
            if action == "start":
                self.proxmox.nodes(node).qemu(vmid).status.start.post()
            elif action == "stop":
                self.proxmox.nodes(node).qemu(vmid).status.stop.post()
            elif action == "reset":
                self.proxmox.nodes(node).qemu(vmid).status.reset.post()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to {action} VM {vmid}: {e}")

    def bulk_remove_vm(self):
        items = self.vm_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "No VM selected.")
            return
        confirm = QMessageBox.question(
            self,
            "Confirm",
            f"Remove {len(items)} VM(s)? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            for item in items:
                self.remove_vm_item(item)
            self.refresh_vms()

    def remove_vm_item(self, item):
        vm_info = item.text()
        parts = vm_info.split(" - ")[0].split(" (ID: ")
        vmid = parts[1][:-1]
        node = vm_info.split(" on ")[-1]
        try:
            self.proxmox.nodes(node).qemu(vmid).delete()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove VM {vmid}: {e}")

    def quick_clone_vm(self):
        items = self.vm_list.selectedItems()
        if not items or len(items) != 1:
            QMessageBox.warning(self, "Warning", "Select exactly ONE VM.")
            return
        vm_info = items[0].text()
        parts = vm_info.split(" - ")[0].split(" (ID: ")
        vmid = parts[1][:-1]
        node = vm_info.split(" on ")[-1]

        new_id, ok = self.simple_input_dialog("Quick Clone", "Enter new VM ID:")
        if not ok or not new_id.isdigit():
            return
        try:
            self.proxmox.nodes(node).qemu(vmid).clone.post(
                newid=int(new_id),
                name=f"clone-of-{vmid}"
            )
            QMessageBox.information(self, "Cloned", f"Cloned VM {vmid} to {new_id}")
            self.refresh_vms()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clone VM: {e}")

    def migrate_vm(self):
        items = self.vm_list.selectedItems()
        if not items or len(items) != 1:
            QMessageBox.warning(self, "Warning", "Select exactly ONE VM.")
            return
        vm_info = items[0].text()
        parts = vm_info.split(" - ")[0].split(" (ID: ")
        vmid = parts[1][:-1]
        node = vm_info.split(" on ")[-1]

        all_nodes = [n['node'] for n in self.proxmox.nodes.get()]
        node_str = ", ".join(all_nodes)
        target_node, ok = self.simple_input_dialog(
            "Migrate VM",
            f"Available nodes: {node_str}\nEnter target node:"
        )
        if not ok or target_node not in all_nodes:
            return
        try:
            self.proxmox.nodes(node).qemu(vmid).migrate.post(target=target_node)
            QMessageBox.information(self, "Migrated", f"VM {vmid} migrated to {target_node}")
            self.refresh_vms()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to migrate VM: {e}")

    def simple_input_dialog(self, title, label):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return (text, ok)
