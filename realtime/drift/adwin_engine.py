"""
ADWIN Drift Detection Engine
"""

from river.drift import ADWIN


class ADWINEngine:

    def __init__(self):

        self.detector = ADWIN()

        self.status = {

            "drift_detected": False,

            "estimation": 0.0
        }

    # ==========================================
    # UPDATE
    # ==========================================

    def update(
        self,
        value: float
    ):

        self.detector.update(
            value
        )

        self.status = {

            "drift_detected":
                self.detector.drift_detected,

            "estimation":
                float(
                    self.detector.estimation
                )
        }

        return self.status

    # ==========================================
    # GET STATUS
    # ==========================================

    def get_status(
        self
    ):

        return self.status