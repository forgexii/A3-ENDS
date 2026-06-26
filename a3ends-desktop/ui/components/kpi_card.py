from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class KPICard(QFrame):
    def __init__(self, title, initial_value="-"):
        super().__init__()
        self.setProperty("class", "Card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "CardTitle")
        
        self.value_label = QLabel(str(initial_value))
        self.value_label.setProperty("class", "CardValue")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))
