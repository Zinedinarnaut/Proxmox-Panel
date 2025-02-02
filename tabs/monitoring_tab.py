# proxmox_manager/tabs/monitoring_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
from PyQt6.QtWidgets import QHeaderView

class MonitoringTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        # Expanded columns: Name, CPU(%), Mem(%), Disk(%), Net In, Net Out
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "VM Name", "CPU (%)", "Memory (%)", "Disk (%)", "Net In (MB)", "Net Out (MB)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def refresh_monitoring(self):
        self.table.setRowCount(0)
        try:
            for node_info in self.proxmox.nodes.get():
                node_name = node_info['node']
                qemus = self.proxmox.nodes(node_name).qemu.get()
                for vm in qemus:
                    row = self.table.rowCount()
                    self.table.insertRow(row)

                    name = vm.get('name', 'N/A')
                    cpu_val = vm.get('cpu', 0.0) * 100
                    maxmem = vm.get('maxmem', 1)
                    mem = vm.get('mem', 0)
                    mem_percent = (mem / maxmem) * 100 if maxmem else 0
                    maxdisk = vm.get('maxdisk', 1)
                    disk = vm.get('disk', 0)
                    disk_percent = (disk / maxdisk) * 100 if maxdisk else 0

                    # net in/out in bytes
                    netin = vm.get('netin', 0)
                    netout = vm.get('netout', 0)
                    netin_mb = netin / (1024.0 * 1024.0)
                    netout_mb = netout / (1024.0 * 1024.0)

                    self.table.setItem(row, 0, QTableWidgetItem(name))
                    self.table.setItem(row, 1, QTableWidgetItem(f"{cpu_val:.2f}"))
                    self.table.setItem(row, 2, QTableWidgetItem(f"{mem_percent:.2f}"))
                    self.table.setItem(row, 3, QTableWidgetItem(f"{disk_percent:.2f}"))
                    self.table.setItem(row, 4, QTableWidgetItem(f"{netin_mb:.2f}"))
                    self.table.setItem(row, 5, QTableWidgetItem(f"{netout_mb:.2f}"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh monitoring: {e}")
