from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
from PyQt6.QtCore import Qt, QTimer
from api_client import ApiClient

class AlertsView(QWidget):
    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()
        self.init_ui()
        
        self.refresh_data()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(10000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Recent Alerts & Incidents")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #F8FAFC; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Timestamp", "Source IP", "Attack Type", "Severity"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)

    def refresh_data(self):
        self.api_client.get_alerts(self.on_data_received, self.on_error)

    def on_data_received(self, data):
        if isinstance(data, list):
            alerts = data
        elif isinstance(data, dict):
            alerts = data.get("alerts", [])
        else:
            alerts = []
            
        self.table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            self.table.setItem(row, 0, QTableWidgetItem(str(alert.get("id"))))
            
            time_str = alert.get("timestamp", "").replace("T", " ")[:19]
            self.table.setItem(row, 1, QTableWidgetItem(time_str))
            
            self.table.setItem(row, 2, QTableWidgetItem(alert.get("source_ip")))
            self.table.setItem(row, 3, QTableWidgetItem(alert.get("attack_type")))
            
            sev_item = QTableWidgetItem(alert.get("severity"))
            sev = alert.get("severity")
            if sev == "CRITICAL":
                sev_item.setForeground(Qt.GlobalColor.red)
            elif sev == "HIGH":
                sev_item.setForeground(Qt.GlobalColor.magenta)
            elif sev == "MEDIUM":
                sev_item.setForeground(Qt.GlobalColor.yellow)
                
            self.table.setItem(row, 4, sev_item)

    def on_error(self, error_msg):
        print(f"Alerts Error: {error_msg}")
