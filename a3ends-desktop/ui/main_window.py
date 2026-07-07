from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt

# We will import the actual views later
from ui.dashboard import DashboardView
from ui.alerts_view import AlertsView
from ws_client import WebSocketClient
from ui.hitl_dialog import HITLDialog
from api_client import ApiClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A3-ENDS - Intrusion Detection System")
        self.resize(1200, 800)
        self.api_client = ApiClient() # Shared API Client
        
        self.init_ui()
        
        self.ws_client = WebSocketClient()
        self.ws_client.health_received.connect(self.on_health_update)
        self.ws_client.alert_received.connect(self.on_new_alert)
        self.ws_client.hitl_received.connect(self.on_hitl_needed)
        self.ws_client.connect_all()

        
    def init_ui(self):
        # Central widget and main layout (HBox for Sidebar + Content)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # App Title
        title_label = QLabel("A3-ENDS")
        title_label.setObjectName("AppTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)
        
        # Navigation Buttons
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setObjectName("NavDashboard")
        self.btn_dashboard.setProperty("class", "SidebarButton")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        self.btn_alerts = QPushButton("Alerts & Incidents")
        self.btn_alerts.setObjectName("NavAlerts")
        self.btn_alerts.setProperty("class", "SidebarButton")
        self.btn_alerts.setCheckable(True)
        
        self.btn_reports = QPushButton("Forensic Reports")
        self.btn_reports.setObjectName("NavReports")
        self.btn_reports.setProperty("class", "SidebarButton")
        self.btn_reports.setCheckable(True)
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_alerts)
        sidebar_layout.addWidget(self.btn_reports)
        sidebar_layout.addStretch() # Push everything up
        
        # Connect buttons
        self.btn_dashboard.clicked.connect(lambda: self.switch_view(0))
        self.btn_alerts.clicked.connect(lambda: self.switch_view(1))
        self.btn_reports.clicked.connect(lambda: self.switch_view(2))
        
        # --- Main Content Area ---
        content_wrapper = QWidget()
        content_wrapper.setObjectName("MainContent")
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top Header
        top_header = QWidget()
        top_header.setObjectName("TopHeader")
        top_header.setFixedHeight(60)
        header_layout = QHBoxLayout(top_header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.status_label = QLabel("SYSTEM ONLINE")
        self.status_label.setObjectName("StatusLabel")
        header_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        content_layout.addWidget(top_header)
        
        # Stacked Widget for Views
        self.stacked_widget = QStackedWidget()
        
        # Add Views
        self.dashboard_view = DashboardView()
        self.alerts_view = AlertsView()
        from ui.reports_view import ReportsView
        self.reports_view = ReportsView()
        
        self.stacked_widget.addWidget(self.dashboard_view)
        self.stacked_widget.addWidget(self.alerts_view)
        self.stacked_widget.addWidget(self.reports_view)
        
        content_layout.addWidget(self.stacked_widget)
        
        # Assemble Main Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_wrapper)
        
    def switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_alerts.setChecked(index == 1)
        self.btn_reports.setChecked(index == 2)

    def on_health_update(self, data):
        status = data.get("status", "UNKNOWN").upper()
        self.status_label.setText(f"SYSTEM {status}")
        self.status_label.setProperty("class", "StatusLabel")
        if status == "OFFLINE":
            self.status_label.setProperty("class", "StatusLabel critical")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def on_new_alert(self, data):
        self.dashboard_view.refresh_data()
        self.alerts_view.refresh_data()

    def on_hitl_needed(self, data):
        print(f"[MAIN-WINDOW] *** HITL SIGNAL RECEIVED! Opening dialog... ***")
        print(f"[MAIN-WINDOW] Data: {data}")
        dialog = HITLDialog(data, self.api_client, self)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog.exec()

