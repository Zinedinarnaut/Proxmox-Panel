# proxmox_manager/tabs/scheduler_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QHBoxLayout, QInputDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, QDateTime
import time

class SchedulerTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

        # A naive list of (vmid, interval_minutes, next_run_ts)
        self.jobs = []
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_jobs)
        self.check_timer.start(10_000)  # check every 10 seconds

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.job_list = QListWidget()
        layout.addWidget(self.job_list)

        btn_layout = QHBoxLayout()
        self.add_job_btn = QPushButton("Add Scheduled Backup")
        self.add_job_btn.clicked.connect(self.add_backup_job)
        btn_layout.addWidget(self.add_job_btn)

        self.remove_job_btn = QPushButton("Remove Job")
        self.remove_job_btn.clicked.connect(self.remove_job)
        btn_layout.addWidget(self.remove_job_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def add_backup_job(self):
        # This is just an example: user picks VMID and interval in minutes
        vmid_str, ok = QInputDialog.getText(self, "Schedule Backup", "Enter VMID:")
        if not ok or not vmid_str.isdigit():
            return
        vmid = int(vmid_str)

        minutes_str, ok2 = QInputDialog.getText(self, "Schedule Backup", "Interval in minutes:")
        if not ok2 or not minutes_str.isdigit():
            return
        interval = int(minutes_str)

        next_run = time.time() + (interval * 60)
        self.jobs.append((vmid, interval, next_run))
        self.refresh_job_list()

    def remove_job(self):
        sel = self.job_list.currentRow()
        if sel < 0:
            return
        del self.jobs[sel]
        self.refresh_job_list()

    def refresh_job_list(self):
        self.job_list.clear()
        for job in self.jobs:
            vmid, interval, next_run = job
            dt = QDateTime.fromSecsSinceEpoch(int(next_run))
            self.job_list.addItem(f"VM {vmid}, every {interval} min, next run: {dt.toString()}")

    def check_jobs(self):
        now = time.time()
        updated = False
        for idx, job in enumerate(self.jobs):
            vmid, interval, next_run = job
            if now >= next_run:
                # Time to run a backup
                node = self.find_vm_node(vmid)
                if node:
                    try:
                        self.proxmox.nodes(node).vzdump.post(
                            vmid=vmid,
                            storage="local",
                            mode="snapshot",
                            compress="lz4"
                        )
                        print(f"Scheduled backup triggered for VM {vmid}")
                    except Exception as e:
                        print(f"Scheduled backup failed for VM {vmid}: {e}")
                else:
                    print(f"Cannot find node for VM {vmid}")

                # Reschedule
                next_run = now + (interval * 60)
                self.jobs[idx] = (vmid, interval, next_run)
                updated = True

        if updated:
            self.refresh_job_list()

    def find_vm_node(self, vmid):
        """Used to find which node a VM is on, same approach as in snapshots_tab."""
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
