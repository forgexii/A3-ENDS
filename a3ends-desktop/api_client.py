import requests
from PyQt6.QtCore import QObject, pyqtSignal, QThread

BASE_URL = "http://127.0.0.1:8000/api"

class ApiWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint

    def run(self):
        try:
            response = requests.get(f"{BASE_URL}/{self.endpoint}", timeout=5)
            response.raise_for_status()
            self.finished.emit(response.json())
        except requests.RequestException as e:
            self.error.emit(str(e))

class ApiClient(QObject):
    def __init__(self):
        super().__init__()
        self.workers = []

    def get_dashboard_data(self, callback, error_callback):
        worker = ApiWorker("dashboard/full")
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        # Keep reference to prevent garbage collection
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()
        
    def get_alerts(self, callback, error_callback):
        worker = ApiWorker("alerts?limit=50")
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def get_reports(self, callback, error_callback):
        worker = ApiWorker("reports/history")
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def generate_report(self, report_type, callback, error_callback):
        worker = ApiPostWorker("reports/generate", data={"report_type": report_type})
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def generate_weekly_report(self, callback, error_callback):
        worker = ApiWorker("reports/weekly")
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

    def resolve_hitl(self, detection_id, action, callback, error_callback):
        # action is one of "approve", "reject", "investigate"
        worker = ApiPostWorker(f"detection/{detection_id}/{action}", data={"notes": "Resolved via desktop UI"})
        worker.finished.connect(callback)
        worker.error.connect(error_callback)
        worker.finished.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        worker.error.connect(lambda: self.workers.remove(worker) if worker in self.workers else None)
        self.workers.append(worker)
        worker.start()

class ApiPostWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, endpoint, data=None):
        super().__init__()
        self.endpoint = endpoint
        self.data = data or {}

    def run(self):
        try:
            response = requests.post(f"{BASE_URL}/{self.endpoint}", json=self.data, timeout=5)
            response.raise_for_status()
            self.finished.emit(response.json())
        except requests.RequestException as e:
            self.error.emit(str(e))
