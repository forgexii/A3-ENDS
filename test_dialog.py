import sys
import os
sys.path.append(os.path.abspath("a3ends-desktop"))
from PyQt6.QtWidgets import QApplication
from ui.hitl_dialog import HITLDialog

class MockAPIClient:
    def resolve_hitl(self, *args, **kwargs):
        pass

def test():
    app = QApplication(sys.argv)
    data = {
        "detection_id": "test_123",
        "timeout_seconds": 5,
        "action": "BLOCK_IP",
        "detection": {
            "attack_type": "ZERO_DAY_ANOMALY",
            "source_ip": "1.1.1.1",
            "confidence": 99.9,
            "shap_explanation": {
                "duration": 5.5,
                "total_bytes": -2.3,
                "packet_count": 1.1
            }
        }
    }
    try:
        dialog = HITLDialog(data, MockAPIClient())
        print("Dialog initialized successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
