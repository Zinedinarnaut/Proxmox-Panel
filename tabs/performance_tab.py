# proxmox_manager/tabs/performance_tab.py

import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCharts import QChart, QChartView, QLineSeries
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt

class PerformanceTab(QWidget):
    def __init__(self, proxmox):
        super().__init__()
        self.proxmox = proxmox
        self.cpu_history = {}  # node_name -> [(timestamp, cpu%)] for performance chart
        self.max_points = 60  # store ~60 data points
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.chart = QChart()
        self.chart.setTitle("Real-Time Node CPU Usage (2s interval)")
        self.chart.legend().setVisible(True)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

    def refresh_performance(self):
        """Query each node's CPU usage, store, and plot."""
        self.chart.removeAllSeries()
        try:
            node_list = self.proxmox.nodes.get()
            for node_info in node_list:
                node_name = node_info['node']
                status = self.proxmox.nodes(node_name).status.get()
                cpu_val = status.get('cpu', 0.0) * 100
                now = time.time()

                if node_name not in self.cpu_history:
                    self.cpu_history[node_name] = []
                self.cpu_history[node_name].append((now, cpu_val))
                if len(self.cpu_history[node_name]) > self.max_points:
                    self.cpu_history[node_name].pop(0)

            # Create a line series for each node
            for node_name, data_points in self.cpu_history.items():
                series = QLineSeries()
                series.setName(node_name)
                start_t = data_points[0][0] if data_points else time.time()
                color = self.pick_color(node_name)
                pen = QPen(QColor(color))
                pen.setWidth(2)
                series.setPen(pen)

                for (ts, cpu) in data_points:
                    x_val = ts - start_t
                    series.append(x_val, cpu)

                self.chart.addSeries(series)

            self.chart.createDefaultAxes()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh performance: {e}")

    def pick_color(self, node_name):
        # Simple hashing for color
        palette = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6",
                   "#bcf60c","#fabebe","#008080","#e6beff","#9a6324","#fffac8","#800000","#aaffc3"]
        return palette[abs(hash(node_name)) % len(palette)]
