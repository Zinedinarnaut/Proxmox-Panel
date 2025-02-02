# proxmox_manager/tabs/ceph_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt

class CephTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.dark_theme = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.ceph_label = QLabel("Ceph Usage / Health")
        layout.addWidget(self.ceph_label)

        self.refresh_btn = QPushButton("Refresh Ceph Status")
        self.refresh_btn.clicked.connect(self.refresh_ceph_status)
        layout.addWidget(self.refresh_btn)

        # Chart to show, for example, OSD usage or # of OSDs up/in
        self.chart = QChart()
        self.chart.setTitle("Ceph OSD Usage")
        self.chart.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.chart.setBackgroundRoundness(0)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

        # We'll also show raw text info
        self.ceph_output = QTextEdit()
        self.ceph_output.setReadOnly(True)
        layout.addWidget(self.ceph_output)

        self.setLayout(layout)

    def refresh_ceph_status(self):
        self.ceph_output.clear()
        self.chart.removeAllSeries()
        try:
            # If using cluster-level ceph
            status = self.proxmox.cluster.ceph.status.get()
            # Display raw info
            self.ceph_output.append(str(status))

            # Build a simple chart
            # For demonstration, let's pretend we have 'osdmap' with 'num_osds', 'num_up_osds', 'num_in_osds'
            osdmap = status.get('osdmap', {})
            total = osdmap.get('num_osds', 0)
            up = osdmap.get('num_up_osds', 0)
            inside = osdmap.get('num_in_osds', 0)
            down = total - up

            series = QPieSeries()
            if total > 0:
                series.append(f"Up ({up})", up)
                series.append(f"Down ({down})", down)
            else:
                # fallback if no OSD info
                series.append("No OSDs Found", 1)

            series.setHoleSize(0.3)  # Donut
            self.chart.addSeries(series)
            self.chart.setTitle(f"Ceph OSDs: total={total}, in={inside}")

            # If dark theme, recolor text
            if self.dark_theme:
                self.chart.setTitleBrush(QColor("white"))
                # For each slice, set label color
                for sl in series.slices():
                    sl.setLabelColor(QColor("white"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch Ceph status: {e}")

    def set_chart_theme(self, dark=False):
        self.dark_theme = dark
        self.refresh_ceph_status()
