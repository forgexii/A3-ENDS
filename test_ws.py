import sys
import json
from PyQt6.QtCore import QCoreApplication, QUrl, QTimer
from PyQt6.QtWebSockets import QWebSocket

def test_ws():
    app = QCoreApplication(sys.argv)
    ws = QWebSocket()
    
    def on_connected():
        print("Connected to ws://127.0.0.1:8000/api/ws/hitl! Waiting for HITL messages...")
        
    def on_message(message):
        try:
            data = json.loads(message)
            print(f"RECEIVED: {data}")
        except Exception:
            print(f"RECEIVED (raw): {message}")
            
    def on_error(err):
        print(f"WebSocket Error: {err}")
        
    ws.connected.connect(on_connected)
    ws.textMessageReceived.connect(on_message)
    ws.errorOccurred.connect(on_error)
    
    url = QUrl("ws://127.0.0.1:8000/api/ws/hitl")
    print(f"Connecting to {url.toString()}...")
    ws.open(url)
    
    return app, ws

if __name__ == "__main__":
    app, ws = test_ws()
    sys.exit(app.exec())
