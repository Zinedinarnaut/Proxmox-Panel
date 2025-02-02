#!/usr/bin/env python3

"""
Proxmox Manager with a dark-themed sidebar using QListWidget and QStackedWidget,
sorted into categories (Compute, Storage, Network & Security, etc.).
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QListWidget, QStackedWidget,
    QVBoxLayout, QLabel, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

from proxmox_connection import get_proxmox

# Import all tabs/pages
from tabs.vm_tab import VmTab
from tabs.create_vm_tab import CreateVMTab
from tabs.monitoring_tab import MonitoringTab
from tabs.performance_tab import PerformanceTab
from tabs.vnc_tab import VNCTab
from tabs.storage_tab import StorageTab
from tabs.network_tab import NetworkTab
from tabs.logs_tab import LogsTab
from tabs.lxc_tab import LXCTab
from tabs.snapshots_tab import SnapshotsTab
from tabs.backup_tab import BackupTab
from tabs.user_mgmt_tab import UserMgmtTab
from tabs.node_summary_tab import NodeSummaryTab
from tabs.scheduler_tab import SchedulerTab
from tabs.ceph_tab import CephTab
from tabs.firewall_tab import FirewallTab
from tabs.firewall_ipset_tab import FirewallIPSetTab
from tabs.firewall_options_tab import FirewallOptionsTab
from tabs.replication_tab import ReplicationTab
from tabs.pools_tab import PoolsTab
from tabs.ha_tab import HATab
from tabs.notifications_tab import NotificationsTab
from tabs.task_log_tab import TaskLogTab
from tabs.vm_details_tab import VmDetailsTab

class ProxmoxGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxmox Manager - Dark Sidebar (with Categories)")
        self.setGeometry(100, 100, 1600, 900)

        # Connect to Proxmox
        self.proxmox = get_proxmox()

        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Dark-themed sidebar (QListWidget)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #efefef;
                border: none;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #444444;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
        """)
        main_layout.addWidget(self.sidebar)

        # Stacked widget for pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages, stretch=1)

        # Instantiate each tab (page)
        # Indices are assigned in the order we addWidget(...)
        self.vm_tab = VmTab(self.proxmox)                # 0
        self.create_vm_tab = CreateVMTab(self.proxmox)   # 1
        self.vm_details_tab = VmDetailsTab(self.proxmox) # 2
        self.monitoring_tab = MonitoringTab(self.proxmox)# 3
        self.performance_tab = PerformanceTab(self.proxmox) # 4
        self.lxc_tab = LXCTab(self.proxmox)              # 5

        self.storage_tab = StorageTab(self.proxmox)      # 6
        self.snapshots_tab = SnapshotsTab(self.proxmox)  # 7
        self.backup_tab = BackupTab(self.proxmox)        # 8

        self.network_tab = NetworkTab(self.proxmox)      # 9
        self.firewall_tab = FirewallTab(self.proxmox)    # 10
        self.firewall_ipset_tab = FirewallIPSetTab(self.proxmox)  # 11
        self.firewall_options_tab = FirewallOptionsTab(self.proxmox)  # 12

        self.logs_tab = LogsTab(self.proxmox)            # 13
        self.node_summary_tab = NodeSummaryTab(self.proxmox)  # 14
        self.scheduler_tab = SchedulerTab(self.proxmox)  # 15
        self.ceph_tab = CephTab(self.proxmox)            # 16
        self.replication_tab = ReplicationTab(self.proxmox) # 17
        self.pools_tab = PoolsTab(self.proxmox)          # 18
        self.ha_tab = HATab(self.proxmox)                # 19

        self.user_mgmt_tab = UserMgmtTab(self.proxmox)   # 20
        self.notifications_tab = NotificationsTab(self.proxmox) # 21
        self.task_log_tab = TaskLogTab(self.proxmox)     # 22

        self.vnc_tab = VNCTab(self.proxmox)              # 23

        # Add pages to the stacked widget in a logical order
        self.pages.addWidget(self.vm_tab)          # index 0
        self.pages.addWidget(self.create_vm_tab)   # index 1
        self.pages.addWidget(self.vm_details_tab)  # index 2
        self.pages.addWidget(self.monitoring_tab)  # index 3
        self.pages.addWidget(self.performance_tab) # index 4
        self.pages.addWidget(self.lxc_tab)         # index 5

        self.pages.addWidget(self.storage_tab)     # index 6
        self.pages.addWidget(self.snapshots_tab)   # index 7
        self.pages.addWidget(self.backup_tab)      # index 8

        self.pages.addWidget(self.network_tab)          # index 9
        self.pages.addWidget(self.firewall_tab)         # index 10
        self.pages.addWidget(self.firewall_ipset_tab)   # index 11
        self.pages.addWidget(self.firewall_options_tab) # index 12

        self.pages.addWidget(self.logs_tab)         # index 13
        self.pages.addWidget(self.node_summary_tab) # index 14
        self.pages.addWidget(self.scheduler_tab)    # index 15
        self.pages.addWidget(self.ceph_tab)         # index 16
        self.pages.addWidget(self.replication_tab)  # index 17
        self.pages.addWidget(self.pools_tab)        # index 18
        self.pages.addWidget(self.ha_tab)           # index 19

        self.pages.addWidget(self.user_mgmt_tab)    # index 20
        self.pages.addWidget(self.notifications_tab)# index 21
        self.pages.addWidget(self.task_log_tab)     # index 22

        self.pages.addWidget(self.vnc_tab)          # index 23

        # Now let's define categories and sub-items
        # We'll create "header" items for each category that are NOT clickable,
        # then real sub-items for each page.

        # Category 1: Compute
        self.add_category("==== Compute ====")
        # - subitems
        self.add_sidebar_item("VMs", 0)
        self.add_sidebar_item("Create VM", 1)
        self.add_sidebar_item("VM Details (Advanced)", 2)
        self.add_sidebar_item("Monitoring", 3)
        self.add_sidebar_item("Performance", 4)
        self.add_sidebar_item("LXC", 5)

        # Category 2: Storage & Backup
        self.add_category("==== Storage & Backup ====")
        self.add_sidebar_item("Storage", 6)
        self.add_sidebar_item("Snapshots", 7)
        self.add_sidebar_item("Backup", 8)

        # Category 3: Network & Security
        self.add_category("==== Network & Security ====")
        self.add_sidebar_item("Network", 9)
        self.add_sidebar_item("Firewall (Rules)", 10)
        self.add_sidebar_item("Firewall (IPSet)", 11)
        self.add_sidebar_item("Firewall (Options)", 12)

        # Category 4: Cluster
        self.add_category("==== Cluster ====")
        self.add_sidebar_item("Logs", 13)
        self.add_sidebar_item("Node Summary", 14)
        self.add_sidebar_item("Scheduler", 15)
        self.add_sidebar_item("Ceph", 16)
        self.add_sidebar_item("Replication", 17)
        self.add_sidebar_item("Pools", 18)
        self.add_sidebar_item("HA", 19)

        # Category 5: Users & Tools
        self.add_category("==== Users & Tools ====")
        self.add_sidebar_item("User Mgmt", 20)
        self.add_sidebar_item("Notifications", 21)
        self.add_sidebar_item("Task Log", 22)

        # Category 6: Additional
        self.add_category("==== Additional ====")
        self.add_sidebar_item("VNC", 23)

        # Connect the signal for item selection
        self.sidebar.currentRowChanged.connect(self.switch_page)

        # Default to the first real item (index 1 in the widget) if you want,
        # but let's do row=1 since row=0 is a category header:
        self.sidebar.setCurrentRow(1)

    def add_category(self, title):
        """
        Add a non-clickable 'header' item to the sidebar.
        """
        category_item = QListWidgetItem(title)
        # Make it unselectable
        category_item.setFlags(Qt.ItemFlag.NoItemFlags)
        font = category_item.font()
        font.setBold(True)
        category_item.setFont(font)
        self.sidebar.addItem(category_item)

    def add_sidebar_item(self, text, page_index):
        """
        Add a clickable sub-item that points to a stacked page index.
        We'll store the page index in Qt.UserRole.
        """
        item = QListWidgetItem(text)
        # We store the page index in item data
        item.setData(Qt.ItemDataRole.UserRole, page_index)
        self.sidebar.addItem(item)

    def switch_page(self, row):
        """
        Switch the stacked widget to the 'row' index, if it's a real item.
        If it's a category item (no flags or no data), do nothing.
        """
        item = self.sidebar.item(row)
        if not item:
            return
        page_index = item.data(Qt.ItemDataRole.UserRole)
        if page_index is not None:
            self.pages.setCurrentIndex(page_index)
        else:
            # It's a category heading, ignore or revert to old selection
            # We'll do a small trick: if the user clicks a category, do nothing
            pass

def main():
    app = QApplication(sys.argv)
    # Optional global dark style
    dark_style = """
    QWidget {
        background-color: #1f1f1f;
        color: #eeeeee;
    }
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QPlainTextEdit {
        background-color: #2b2b2b;
        color: #ffffff;
        border: 1px solid #444;
    }
    QPushButton {
        background-color: #3a3a3a;
        color: #ffffff;
        border: 1px solid #444444;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QListWidget, QTableWidget, QTreeWidget {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    """
    app.setStyleSheet(dark_style)

    window = ProxmoxGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
