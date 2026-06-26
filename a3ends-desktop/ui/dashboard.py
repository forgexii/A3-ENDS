from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QFrame
from PyQt6.QtCore import Qt, QTimer
from ui.components.kpi_card import KPICard
from api_client import ApiClient

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()
        self.init_ui()
        
        # Initial load
        self.refresh_data()
        
        # Setup polling timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10000) # 10 seconds

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # --- Top KPIs ---
        kpi_layout = QHBoxLayout()
        self.card_flows = KPICard("Total Flows")
        self.card_alerts = KPICard("Total Alerts")
        self.card_critical = KPICard("Critical Incidents")
        self.card_accuracy = KPICard("Detection Accuracy")
        
        kpi_layout.addWidget(self.card_flows)
        kpi_layout.addWidget(self.card_alerts)
        kpi_layout.addWidget(self.card_critical)
        kpi_layout.addWidget(self.card_accuracy)
        
        layout.addLayout(kpi_layout)
        
        # --- Middle Area (Chart + Feed) ---
        middle_layout = QHBoxLayout()
        
        # Chart
        chart_frame = QFrame()
        chart_frame.setProperty("class", "Card")
        chart_layout = QVBoxLayout(chart_frame)
        chart_title = QLabel("Attack Distribution")
        chart_title.setProperty("class", "CardTitle")
        chart_layout.addWidget(chart_title)
        
        self.figure = Figure(figsize=(5, 4), facecolor='#1E293B')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1E293B')
        self.ax.tick_params(colors='#94A3B8')
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#334155')
            
        chart_layout.addWidget(self.canvas)
        middle_layout.addWidget(chart_frame, stretch=2)
        
        # Activity Feed
        feed_frame = QFrame()
        feed_frame.setProperty("class", "Card")
        feed_layout = QVBoxLayout(feed_frame)
        feed_title = QLabel("Recent Activity")
        feed_title.setProperty("class", "CardTitle")
        feed_layout.addWidget(feed_title)
        
        self.feed_list = QListWidget()
        self.feed_list.setStyleSheet("QListWidget { background: transparent; border: none; } QListWidget::item { padding: 8px; border-bottom: 1px solid #334155; }")
        feed_layout.addWidget(self.feed_list)
        
        middle_layout.addWidget(feed_frame, stretch=1)
        
        layout.addLayout(middle_layout, stretch=1)

    def refresh_data(self):
        self.api_client.get_dashboard_data(self.on_data_received, self.on_error)

    def on_data_received(self, data):
        if not isinstance(data, dict):
            return
            
        # Update KPIs
        self.card_flows.set_value(data.get("total_flows", 0))
        self.card_alerts.set_value(data.get("total_alerts", 0))
        self.card_critical.set_value(data.get("critical_incidents", 0))
        acc = data.get("detection_accuracy", 0)
        self.card_accuracy.set_value(f"{acc:.1f}%")
        
        # Update Feed
        self.feed_list.clear()
        events = data.get("activity_events", [])
        for evt in events:
            time_str = evt.get("timestamp", "")
            msg = evt.get("message", "")
            self.feed_list.addItem(f"[{time_str}] {msg}")
            
        # Update Chart
        dist = data.get("attack_distribution", [])
        self.ax.clear()
        
        labels = [item["name"] for item in dist if item["name"] != "Normal"]
        values = [item["value"] for item in dist if item["name"] != "Normal"]
        
        if labels and values:
            colors = ['#06B6D4', '#EF4444', '#F59E0B', '#8B5CF6', '#10B981']
            self.ax.pie(values, labels=labels, autopct='%1.1f%%', textprops={'color': '#E2E8F0'}, colors=colors)
        else:
            self.ax.text(0.5, 0.5, "No attack data", color='#94A3B8', ha='center', va='center')
            
        self.canvas.draw()

    def on_error(self, error_msg):
        print(f"Dashboard Error: {error_msg}")
