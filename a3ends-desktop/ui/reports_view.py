from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from api_client import ApiClient
import webbrowser

class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.api_client = ApiClient()
        self.init_ui()
        
        self.refresh_data()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000) # Poll every 5 seconds for status updates

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Area
        header_layout = QHBoxLayout()
        title = QLabel("Forensic & Executive Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #F8FAFC; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Generate Buttons
        btn_pdf = QPushButton("Generate Single Incident Report (PDF)")
        btn_pdf.setStyleSheet("background-color: #3B82F6; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_pdf.clicked.connect(lambda: self.generate_report("pdf"))
        
        btn_weekly = QPushButton("Generate Weekly SOC Report")
        btn_weekly.setStyleSheet("background-color: #10B981; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_weekly.clicked.connect(self.generate_weekly)

        header_layout.addWidget(btn_pdf)
        header_layout.addWidget(btn_weekly)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Report ID", "Type", "Status", "Generated At", "Action"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)

    def refresh_data(self):
        self.api_client.get_reports(self.on_data_received, self.on_error)

    def on_data_received(self, data):
        if isinstance(data, dict):
            reports = data.get("reports", [])
        elif isinstance(data, list):
            reports = data
        else:
            reports = []
            
        self.table.setRowCount(len(reports))
        
        for row, report in enumerate(reports):
            self.table.setItem(row, 0, QTableWidgetItem(str(report.get("report_id"))))
            
            # Type styling
            rtype = report.get("report_type", "").upper()
            self.table.setItem(row, 1, QTableWidgetItem(rtype))
            
            # Status styling
            status = report.get("status", "")
            status_item = QTableWidgetItem(status)
            if status == "COMPLETE":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "PENDING":
                status_item.setForeground(Qt.GlobalColor.yellow)
            elif status == "FAILED":
                status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)
            
            time_str = report.get("generated_at", "").replace("T", " ")[:19]
            self.table.setItem(row, 3, QTableWidgetItem(time_str))
            
            # Download Button
            if status == "COMPLETE":
                dl_btn = QPushButton("Download")
                dl_btn.setStyleSheet("background-color: #0F172A; color: #22D3EE; border: 1px solid #22D3EE; padding: 4px; border-radius: 3px;")
                dl_btn.clicked.connect(lambda checked, rid=report.get("report_id"), rt=rtype: self.download_report(rid, rt))
                self.table.setCellWidget(row, 4, dl_btn)
            else:
                self.table.removeCellWidget(row, 4)
                self.table.setItem(row, 4, QTableWidgetItem(""))

    def on_error(self, error_msg):
        print(f"Reports Error: {error_msg}")

    def generate_report(self, rtype):
        self.api_client.generate_report(rtype, self.on_generate_success, self.on_error)
        QMessageBox.information(self, "Generating", f"Started generation for {rtype.upper()} report. It will appear in the table shortly.")
        self.refresh_data()

    def generate_weekly(self):
        self.api_client.generate_weekly_report(self.on_generate_success, self.on_error)
        QMessageBox.information(self, "Generating", "Started generation for Weekly SOC Report. This aggregates a lot of data and uses the LLM, so it will take a moment.")
        self.refresh_data()

    def on_generate_success(self, data):
        self.refresh_data()

    def download_report(self, report_id, rtype):
        from PyQt6.QtWidgets import QFileDialog
        import requests
        
        ext = rtype.lower()
        if ext not in ["pdf", "json"]:
            ext = "pdf" # Default to pdf if type mapping was overwritten backend-side
        
        default_name = f"report_{report_id}.{ext}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            default_name,
            f"{ext.upper()} Files (*.{ext});;All Files (*)"
        )
        
        if file_path:
            url = f"http://127.0.0.1:8000/api/reports/download/{report_id}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    f.write(response.content)
                QMessageBox.information(self, "Success", f"Report saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to download report:\n{str(e)}")
