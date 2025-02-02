# proxmox_manager/tabs/create_vm_tab.py
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QHBoxLayout
)

class CreateVMTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Node selection
        self.node_label = QLabel("Select Node")
        layout.addWidget(self.node_label)
        self.node_combo = QComboBox()
        try:
            node_list = [n['node'] for n in self.proxmox.nodes.get()]
        except Exception:
            node_list = ["pve"]
        self.node_combo.addItems(node_list)
        layout.addWidget(self.node_combo)

        # VM Name
        self.vm_name_label = QLabel("VM Name")
        layout.addWidget(self.vm_name_label)
        self.vm_name_input = QLineEdit()
        layout.addWidget(self.vm_name_input)

        # Memory
        self.vm_memory_label = QLabel("Memory (MB)")
        layout.addWidget(self.vm_memory_label)
        self.vm_memory_spin = QSpinBox()
        self.vm_memory_spin.setRange(1, 131072)  # up to 128 GB
        self.vm_memory_spin.setValue(2048)
        layout.addWidget(self.vm_memory_spin)

        # CPU Cores
        self.vm_cpu_label = QLabel("Number of CPU Cores")
        layout.addWidget(self.vm_cpu_label)
        self.vm_cpu_spin = QSpinBox()
        self.vm_cpu_spin.setRange(1, 64)
        self.vm_cpu_spin.setValue(2)
        layout.addWidget(self.vm_cpu_spin)

        # CPU Type selection
        self.cpu_type_label = QLabel("CPU Type")
        layout.addWidget(self.cpu_type_label)
        self.cpu_type_combo = QComboBox()
        # Common CPU types: 'kvm64', 'host', 'qemu64', etc.
        self.cpu_type_combo.addItems(["kvm64", "host", "qemu64", "Broadwell", "Skylake"])
        layout.addWidget(self.cpu_type_combo)

        # BIOS type
        self.bios_label = QLabel("BIOS Type")
        layout.addWidget(self.bios_label)
        self.bios_combo = QComboBox()
        # 'seabios' (legacy) or 'ovmf' (UEFI)
        self.bios_combo.addItems(["seabios", "ovmf"])
        layout.addWidget(self.bios_combo)

        # Machine type
        self.machine_label = QLabel("Machine Type")
        layout.addWidget(self.machine_label)
        self.machine_combo = QComboBox()
        # Common: 'pc' (legacy) or 'q35' (modern)
        self.machine_combo.addItems(["pc", "q35"])
        layout.addWidget(self.machine_combo)

        # Disk size
        self.vm_disk_label = QLabel("Disk Size (GB)")
        layout.addWidget(self.vm_disk_label)
        self.vm_disk_spin = QSpinBox()
        self.vm_disk_spin.setRange(1, 2000)
        self.vm_disk_spin.setValue(20)
        layout.addWidget(self.vm_disk_spin)

        # Storage selection
        self.storage_label = QLabel("Storage for Disk")
        layout.addWidget(self.storage_label)
        self.storage_combo = QComboBox()
        self.populate_storage_combo()
        layout.addWidget(self.storage_combo)

        # ISO selection
        self.iso_label = QLabel("ISO Image")
        layout.addWidget(self.iso_label)
        self.iso_combo = QComboBox()
        self.populate_iso_combo()
        layout.addWidget(self.iso_combo)

        # Basic network bridging
        self.net_label = QLabel("Bridge for Net0 (Virtio)")
        layout.addWidget(self.net_label)
        self.net_combo = QComboBox()
        # A typical default is 'vmbr0'. If you want to discover from Proxmox, you can do so.
        self.net_combo.addItems(["vmbr0", "vmbr1"])
        layout.addWidget(self.net_combo)

        # Create button
        self.create_vm_button = QPushButton("Create VM")
        self.create_vm_button.clicked.connect(self.create_vm)
        layout.addWidget(self.create_vm_button)

        self.setLayout(layout)

    def populate_storage_combo(self):
        self.storage_combo.clear()
        node = self.node_combo.currentText() or "pve"
        try:
            storages = self.proxmox.nodes(node).storage.get()
            for st in storages:
                if 'content' in st and 'images' in st['content'].split(","):
                    self.storage_combo.addItem(st['storage'])
        except Exception as e:
            print(f"Failed to populate storage combo: {e}")

    def populate_iso_combo(self):
        self.iso_combo.clear()
        node = self.node_combo.currentText() or "pve"
        try:
            storages = self.proxmox.nodes(node).storage.get()
            iso_list = []
            for st in storages:
                if 'content' in st and 'iso' in st['content'].split(","):
                    storage_name = st['storage']
                    content = self.proxmox.nodes(node).storage(storage_name).content.get()
                    for item in content:
                        if item.get('content') == 'iso':
                            iso_list.append((storage_name, item['volid']))
            for storage_name, volid in iso_list:
                self.iso_combo.addItem(f"{storage_name}:{volid}")
        except Exception as e:
            print(f"Failed to populate ISO combo: {e}")

    def create_vm(self):
        node = self.node_combo.currentText() or "pve"
        vm_name = self.vm_name_input.text().strip()
        vm_memory = self.vm_memory_spin.value()
        vm_cpu = self.vm_cpu_spin.value()
        cpu_type = self.cpu_type_combo.currentText()
        bios_type = self.bios_combo.currentText()  # 'seabios' or 'ovmf'
        machine_type = self.machine_combo.currentText()  # 'pc' or 'q35'

        vm_disk_size = self.vm_disk_spin.value()
        storage_name = self.storage_combo.currentText()
        iso_volid = self.iso_combo.currentText()

        bridge_name = self.net_combo.currentText()  # e.g. vmbr0

        if not vm_name:
            QMessageBox.warning(self, "Warning", "Please specify a VM name.")
            return

        # generate a naive new VM ID
        new_vmid = 100 + len(self.list_vms())
        try:
            # Step 1: create the base VM config
            self.proxmox.nodes(node).qemu.post(
                vmid=new_vmid,
                name=vm_name,
                memory=vm_memory,
                cores=vm_cpu,
                cpu=cpu_type,  # advanced CPU type
                bios=bios_type,
                machine=machine_type,
                scsihw="virtio-scsi-pci",
                sata0=f"{storage_name}:iso/{iso_volid}",
                boot="cdrom",
                bootdisk="scsi0"
            )

            # Step 2: Allocate disk
            disk_params = {
                "vmid": new_vmid,
                "size": f"{vm_disk_size}G",
                "storage": storage_name,
                "disk": "scsi0",
                "cache": "writeback"
            }
            self.proxmox.nodes(node).qemu.post(**disk_params)

            # Step 3: Configure net0 bridging, using virtio model
            net_params = {
                "net0": f"virtio,bridge={bridge_name}"
            }
            self.proxmox.nodes(node).qemu(new_vmid).config.put(**net_params)

            QMessageBox.information(self, "Success", f"Created VM {vm_name} with ID {new_vmid}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create VM: {e}")

    def list_vms(self):
        """
        Helper to count existing VMs for new_vmid calc.
        """
        vm_list = []
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                qemus = self.proxmox.nodes(node_name).qemu.get()
                for vm in qemus:
                    vm_list.append(vm)
        except:
            pass
        return vm_list
