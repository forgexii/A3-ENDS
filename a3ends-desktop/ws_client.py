import json
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtWebSockets import QWebSocket

WS_BASE_URL = "ws://127.0.0.1:8000/api/ws"

class WebSocketClient(QObject):
    alert_received = pyqtSignal(dict)
    health_received = pyqtSignal(dict)
    hitl_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        
        # Alerts Socket
        self.ws_alerts = QWebSocket()
        self.ws_alerts.textMessageReceived.connect(self._on_alert_message)
        self.ws_alerts.connected.connect(lambda: print("WS Alerts Connected"))
        
        # Health Socket
        self.ws_health = QWebSocket()
        self.ws_health.textMessageReceived.connect(self._on_health_message)
        
        # HITL Socket
        self.ws_hitl = QWebSocket()
        self.ws_hitl.textMessageReceived.connect(self._on_hitl_message)
        self.ws_hitl.connected.connect(lambda: print("WS HITL Connected"))
        
    def connect_all(self):
        self.ws_alerts.open(QUrl(f"{WS_BASE_URL}/alerts"))
        self.ws_health.open(QUrl(f"{WS_BASE_URL}/health"))
        self.ws_hitl.open(QUrl(f"{WS_BASE_URL}/hitl"))

    def _on_alert_message(self, message):
        try:
            data = json.loads(message)
            if data.get("type") == "new_alert":
                self.alert_received.emit(data.get("data", {}))
        except json.JSONDecodeError:
            pass

    def _on_health_message(self, message):
        try:
            data = json.loads(message)
            if data.get("type") == "health_update":
                self.health_received.emit(data)
        except json.JSONDecodeError:
            pass

    def _on_hitl_message(self, message):
        try:
            data = json.loads(message)
            if data.get("type") == "approval_needed":
                self.hitl_received.emit(data.get("data", {}))
        except json.JSONDecodeError:
            pass
