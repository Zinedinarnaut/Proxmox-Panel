# proxmox_manager/tabs/node_summary_tab.py

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt

class NodeSummaryTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.setup_ui()

        self.cpu_history = {}  # node_name -> [(timestamp, cpu_percent), ...]
        self.max_history_points = 50
        self.dark_theme = False

    def setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Node Summary (Enhanced Graph, Dark Mode Support)")
        layout.addWidget(label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Node", "CPU Usage", "Memory Usage", "Load Avg"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.chart = QChart()
        self.chart.setTitle("Node CPU Usage Over Time")
        # Make chart background transparent
        self.chart.setBackgroundRoundness(0)
        self.chart.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.chart.legend().setVisible(True)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

        self.refresh_btn = QPushButton("Refresh Node Summary")
        self.refresh_btn.clicked.connect(self.refresh_node_summary)
        layout.addWidget(self.refresh_btn)

        self.setLayout(layout)

    def refresh_node_summary(self):
        self.table.setRowCount(0)
        try:
            self.chart.removeAllSeries()
            nodes = self.proxmox.nodes.get()

            for node_info in nodes:
                node_name = node_info['node']
                status = self.proxmox.nodes(node_name).status.get()

                cpu_val = status.get('cpu', 0.0) * 100
                mem_total = status.get('memory', {}).get('total', 1)
                mem_used = status.get('memory', {}).get('used', 0)
                mem_percent = (mem_used / mem_total) * 100 if mem_total else 0

                load_list = status.get('loadavg', [0, 0, 0])
                load_1m = load_list[0] if load_list else 0

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(node_name))
                self.table.setItem(row, 1, QTableWidgetItem(f"{cpu_val:.2f}%"))
                self.table.setItem(
                    row, 2,
                    QTableWidgetItem(f"{mem_percent:.2f}% ({mem_used // 1024**2}/{mem_total // 1024**2} MB)")
                )
                self.table.setItem(row, 3, QTableWidgetItem(str(load_1m)))

                # Update CPU history
                if node_name not in self.cpu_history:
                    self.cpu_history[node_name] = []
                now = time.time()
                self.cpu_history[node_name].append((now, cpu_val))
                if len(self.cpu_history[node_name]) > self.max_history_points:
                    self.cpu_history[node_name].pop(0)

            # Plot each node
            for node_name, datapoints in self.cpu_history.items():
                series = QLineSeries()
                series.setName(node_name)
                if datapoints:
                    start_time = datapoints[0][0]
                else:
                    start_time = time.time()
                color = self.get_node_color(node_name)
                pen = QPen(QColor(color))
                pen.setWidth(2)
                series.setPen(pen)

                for (ts, cpu_percent) in datapoints:
                    x_val = ts - start_time
                    series.append(x_val, cpu_percent)

                self.chart.addSeries(series)

            self.chart.createDefaultAxes()
            # If using dark theme, set axis color to a lighter color
            if self.dark_theme:
                for axis in self.chart.axes():
                    axis.setLabelsColor(QColor("white"))
                    axis.setLinePenColor(QColor("white"))
                    axis.setGridLineColor(QColor("#888"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get node summary: {e}")

    def set_chart_theme(self, dark=False):
        self.dark_theme = dark
        # Re-plot so axis colors get updated
        self.refresh_node_summary()

    def get_node_color(self, node_name):
        """
        Return a color string used for the line series.
        Could do a map from node_name to colors for consistency.
        """
        # Just pick from a small palette for demonstration
        palette = [
            "#ff5555", "#55ff55", "#5555ff", "#ffff55",
            "#55ffff", "#ff55ff", "#ffa500", "#00a500"
        ]
        # Hash node_name to pick a color
        idx = abs(hash(node_name)) % len(palette)
        return palette[idx]
