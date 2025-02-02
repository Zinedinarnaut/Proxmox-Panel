# proxmox_manager/tabs/vm_details_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QSpinBox,
    QMessageBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt

class VmDetailsTab(QWidget):
    """
    A tab for advanced VM controls: load a specific VM’s config, change CPU/memory,
    resize disk, migrate, clone, etc.
    """
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Row 1: Node + VMID + 'Load' button
        row1 = QHBoxLayout()
        self.node_input = QLineEdit()
        self.node_input.setPlaceholderText("Node (e.g. pve)")
        row1.addWidget(self.node_input)

        self.vmid_input = QLineEdit()
        self.vmid_input.setPlaceholderText("VMID (e.g. 101)")
        row1.addWidget(self.vmid_input)

        self.load_btn = QPushButton("Load VM Config")
        self.load_btn.clicked.connect(self.load_vm_config)
        row1.addWidget(self.load_btn)

        layout.addLayout(row1)

        # VM config fields
        # CPU
        cpu_row = QHBoxLayout()
        cpu_label = QLabel("CPU Cores:")
        cpu_row.addWidget(cpu_label)
        self.cpu_spin = QSpinBox()
        self.cpu_spin.setRange(1, 128)
        cpu_row.addWidget(self.cpu_spin)
        layout.addLayout(cpu_row)

        # Memory
        mem_row = QHBoxLayout()
        mem_label = QLabel("Memory (MB):")
        mem_row.addWidget(mem_label)
        self.mem_spin = QSpinBox()
        self.mem_spin.setRange(1, 262144)  # up to 256GB for example
        mem_row.addWidget(self.mem_spin)
        layout.addLayout(mem_row)

        # Some extra checkboxes (hotplug, balloon, etc.)
        extra_opts_layout = QHBoxLayout()
        self.hotplug_cb = QCheckBox("Hotplug CPU/Memory")
        extra_opts_layout.addWidget(self.hotplug_cb)

        self.balloon_cb = QCheckBox("Ballooning")
        extra_opts_layout.addWidget(self.balloon_cb)

        layout.addLayout(extra_opts_layout)

        # Button to update config
        self.update_config_btn = QPushButton("Update VM Config")
        self.update_config_btn.clicked.connect(self.update_vm_config)
        layout.addWidget(self.update_config_btn)

        # Disk resize
        disk_resize_layout = QHBoxLayout()
        self.resize_label = QLabel("Resize Disk:")
        disk_resize_layout.addWidget(self.resize_label)
        self.disk_input = QLineEdit()
        self.disk_input.setPlaceholderText("Disk name (e.g. scsi0)")
        disk_resize_layout.addWidget(self.disk_input)

        self.resize_spin = QSpinBox()
        self.resize_spin.setRange(1, 10000)  # up to 10 TB extra?
        self.resize_spin.setValue(10)
        disk_resize_layout.addWidget(self.resize_spin)

        self.resize_btn = QPushButton("Add (GB)")
        self.resize_btn.clicked.connect(self.resize_disk)
        disk_resize_layout.addWidget(self.resize_btn)
        layout.addLayout(disk_resize_layout)

        # Migrate
        migrate_layout = QHBoxLayout()
        self.migrate_label = QLabel("Migrate to:")
        migrate_layout.addWidget(self.migrate_label)
        self.migrate_target_combo = QComboBox()
        migrate_layout.addWidget(self.migrate_target_combo)
        self.migrate_btn = QPushButton("Migrate VM")
        self.migrate_btn.clicked.connect(self.migrate_vm)
        migrate_layout.addWidget(self.migrate_btn)
        layout.addLayout(migrate_layout)

        # Clone
        clone_layout = QHBoxLayout()
        self.clone_label = QLabel("Clone to new VMID:")
        clone_layout.addWidget(self.clone_label)
        self.clone_vmid_input = QLineEdit()
        self.clone_vmid_input.setPlaceholderText("e.g. 200")
        clone_layout.addWidget(self.clone_vmid_input)
        self.clone_btn = QPushButton("Clone VM")
        self.clone_btn.clicked.connect(self.clone_vm)
        clone_layout.addWidget(self.clone_btn)
        layout.addLayout(clone_layout)

        self.setLayout(layout)

        # Optionally, populate migrate_target_combo with node names:
        self.load_node_list()

    def load_node_list(self):
        """Load the list of nodes into the migrate_target_combo for migration target selection."""
        self.migrate_target_combo.clear()
        try:
            node_list = self.proxmox.nodes.get()
            for n in node_list:
                self.migrate_target_combo.addItem(n['node'])
        except:
            pass

    def load_vm_config(self):
        """GET /nodes/{node}/qemu/{vmid}/config -> load CPU/mem/hotplug/balloon, etc."""
        node = self.node_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not vmid_str.isdigit():
            QMessageBox.warning(self, "Warning", "VMID invalid.")
            return
        vmid = int(vmid_str)
        try:
            config = self.proxmox.nodes(node).qemu(vmid).config.get()
            # e.g. config might have 'cores', 'memory', 'hotplug', 'balloon', etc.
            cores = config.get('cores', 1)
            mem = config.get('memory', 1024)
            hotplug = config.get('hotplug', "")
            balloon = config.get('balloon', 0)

            self.cpu_spin.setValue(int(cores))
            self.mem_spin.setValue(int(mem))
            # hotplug might be a comma-separated list: e.g. 'disk,network,usb'
            # if it contains 'cpu' or 'memory', we check hotplug
            self.hotplug_cb.setChecked(('cpu' in hotplug) or ('memory' in hotplug))
            # balloon is 1 or 0
            self.balloon_cb.setChecked(bool(balloon))

            QMessageBox.information(self, "Loaded", f"Loaded VM config for {vmid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load VM config: {e}")

    def update_vm_config(self):
        """
        PUT /nodes/{node}/qemu/{vmid}/config
        CPU cores = cores=...
        Memory = memory=...
        hotplug=... (like 'cpu,memory,disk' or none)
        balloon=1 or 0
        """
        node = self.node_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not vmid_str.isdigit():
            return
        vmid = int(vmid_str)
        cores = self.cpu_spin.value()
        memory = self.mem_spin.value()

        hotplug_opts = []
        if self.hotplug_cb.isChecked():
            # for demonstration, let's say we only do 'cpu,memory'
            hotplug_opts = ['cpu','memory']
        hotplug_str = ",".join(hotplug_opts)  # e.g. "cpu,memory"

        balloon_val = 1 if self.balloon_cb.isChecked() else 0

        try:
            self.proxmox.nodes(node).qemu(vmid).config.put(
                cores=cores,
                memory=memory,
                hotplug=hotplug_str,
                balloon=balloon_val
            )
            QMessageBox.information(self, "Updated", "VM config updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update VM: {e}")

    def resize_disk(self):
        """
        POST /nodes/{node}/qemu/{vmid}/resize
        fields: disk=scsi0, size=+10G, etc.
        We'll do size=+XG where X is from spin box
        """
        node = self.node_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not vmid_str.isdigit():
            return
        vmid = int(vmid_str)
        disk = self.disk_input.text().strip()
        if not disk:
            QMessageBox.warning(self, "Warning", "Enter disk name (e.g. scsi0).")
            return
        size_gb = self.resize_spin.value()
        size_str = f"+{size_gb}G"
        try:
            self.proxmox.nodes(node).qemu(vmid).resize.post(
                disk=disk,
                size=size_str
            )
            QMessageBox.information(self, "Resized", f"Disk {disk} resized by {size_gb} GB.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to resize disk: {e}")

    def migrate_vm(self):
        """
        POST /nodes/{node}/qemu/{vmid}/migrate
        fields: target=..., online=..., etc.
        """
        node = self.node_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        if not vmid_str.isdigit():
            return
        vmid = int(vmid_str)
        target_node = self.migrate_target_combo.currentText()
        try:
            self.proxmox.nodes(node).qemu(vmid).migrate.post(
                target=target_node
            )
            QMessageBox.information(self, "Migrating", f"VM {vmid} migrating to {target_node}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to migrate VM: {e}")

    def clone_vm(self):
        """
        POST /nodes/{node}/qemu/{vmid}/clone
        fields: newid=..., name=..., target=..., full=1 or 0, etc.
        """
        node = self.node_input.text().strip()
        vmid_str = self.vmid_input.text().strip()
        cloneid_str = self.clone_vmid_input.text().strip()
        if not (vmid_str.isdigit() and cloneid_str.isdigit()):
            return
        vmid = int(vmid_str)
        new_vmid = int(cloneid_str)
        confirm = QMessageBox.question(
            self,
            "Clone",
            f"Clone VM {vmid} to new VMID {new_vmid}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.proxmox.nodes(node).qemu(vmid).clone.post(
                    newid=new_vmid,
                    name=f"clone-{new_vmid}"
                )
                QMessageBox.information(self, "Cloned", f"Cloned VM {vmid} to {new_vmid}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clone VM: {e}")
