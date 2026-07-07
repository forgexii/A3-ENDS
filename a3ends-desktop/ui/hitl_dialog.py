from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QWidget
from PyQt6.QtCore import Qt, QTimer
import json

class HITLDialog(QDialog):
    def __init__(self, data, api_client, parent=None):
        super().__init__(parent)
        self.data = data
        self.api_client = api_client
        self.detection_id = data.get("detection_id")
        self.timeout = data.get("timeout_seconds", 30)
        
        self.setWindowTitle("ACTION REQUIRED - HITL")
        self.setMinimumSize(520, 500)
        self.setMaximumSize(600, 700)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setStyleSheet("QDialog { background-color: #0F172A; border: 2px solid #EF4444; border-radius: 8px; }")
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⚠️ ACTION REQUIRED: Auto-Response Intercepted")
        title.setStyleSheet("color: #EF4444; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #1E293B; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #475569; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)
        
        # Details Frame
        frame = QFrame()
        frame.setStyleSheet("background-color: #1E293B; border-radius: 6px; padding: 10px;")
        frame_layout = QVBoxLayout(frame)
        
        detection = self.data.get("detection", {})
        action = self.data.get("action", "UNKNOWN")
        
        lbl_action = QLabel(f"<b>Proposed Action:</b> <span style='color: #F59E0B;'>{action}</span>")
        lbl_attack = QLabel(f"<b>Attack Type:</b> {detection.get('attack_type', 'Unknown')}")
        lbl_src = QLabel(f"<b>Source IP:</b> {detection.get('source_ip', 'Unknown')}")
        lbl_conf = QLabel(f"<b>Confidence:</b> {detection.get('confidence', 0)}%")
        
        for lbl in [lbl_action, lbl_attack, lbl_src, lbl_conf]:
            lbl.setStyleSheet("color: #E2E8F0; font-size: 14px;")
            frame_layout.addWidget(lbl)
            
        # Add SHAP explanation if available
        shap_data = detection.get("shap_explanation")
        if shap_data and isinstance(shap_data, dict):
            lbl_shap = QLabel("<b>AI Decision Drivers (SHAP):</b>")
            lbl_shap.setStyleSheet("color: #E2E8F0; font-size: 14px; margin-top: 10px;")
            frame_layout.addWidget(lbl_shap)
            
            # Show ALL SHAP features, sorted by absolute importance
            shap_text = ""
            sorted_shap = sorted(shap_data.items(), key=lambda x: abs(float(x[1])), reverse=True)
            for feature, importance in sorted_shap:
                color = "#EF4444" if float(importance) > 0 else "#22C55E"
                direction = "▲" if float(importance) > 0 else "▼"
                shap_text += f"• {feature}: <span style='color: {color};'>{direction} {float(importance):.4f}</span><br>"
            
            lbl_shap_val = QLabel(shap_text)
            lbl_shap_val.setStyleSheet("color: #94A3B8; font-size: 13px;")
            lbl_shap_val.setWordWrap(True)
            frame_layout.addWidget(lbl_shap_val)
        
        scroll_layout.addWidget(frame)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)  # stretch factor 1 so it fills space
        
        # Timer
        self.lbl_timer = QLabel(f"Time remaining: {self.timeout}s")
        self.lbl_timer.setStyleSheet("color: #EF4444; font-size: 16px; font-weight: bold;")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_timer)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_accept = QPushButton("Approve")
        self.btn_accept.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        self.btn_accept.clicked.connect(lambda: self.resolve("approve"))
        
        self.btn_reject = QPushButton("Reject")
        self.btn_reject.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        self.btn_reject.clicked.connect(lambda: self.resolve("reject"))
        
        self.btn_investigate = QPushButton("Investigate")
        self.btn_investigate.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        self.btn_investigate.clicked.connect(lambda: self.resolve("investigate"))
        
        btn_layout.addWidget(self.btn_accept)
        btn_layout.addWidget(self.btn_investigate)
        btn_layout.addWidget(self.btn_reject)
        
        layout.addLayout(btn_layout)

    def tick(self):
        self.timeout -= 1
        self.lbl_timer.setText(f"Time remaining: {self.timeout}s")
        if self.timeout <= 0:
            self.timer.stop()
            self.reject() # Close dialog

    def resolve(self, action):
        self.timer.stop()
        self.api_client.resolve_hitl(
            self.detection_id, 
            action, 
            self.on_resolve_success, 
            self.on_resolve_error
        )
        self.accept()

    def on_resolve_success(self, response):
        pass # Dialog already closed

    def on_resolve_error(self, error):
        print(f"Failed to resolve HITL: {error}")
