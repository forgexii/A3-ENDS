"""
Risk Engine

Calculates threat severity and
risk scores from AI detections.
"""


class RiskEngine:

    def __init__(self):

        self.attack_names = {
            "BENIGN": "BENIGN",
            "PortScan": "PORTSCAN",
            "DoS GoldenEye": "DOS",
            "DoS Hulk": "DOS",
            "DoS Slowhttptest": "DOS",
            "DoS slowloris": "DOS",
            "DDoS": "DDOS",
            "FTP-Patator": "BRUTE_FORCE",
            "SSH-Patator": "BRUTE_FORCE",
            "Bot": "BOTNET",
            "Web Attack \ufffd Brute Force": "WEB_ATTACK",
            "Web Attack \ufffd Sql Injection": "WEB_ATTACK",
            "Web Attack \ufffd XSS": "WEB_ATTACK",
            "Heartbleed": "WEB_ATTACK",
            "Infiltration": "INFILTRATION"
        }

        self.base_weights = {

            "BENIGN": 0,

            "PORTSCAN": 30,

            "DOS": 60,

            "DDOS": 85,

            "BRUTE_FORCE": 70,

            "BOTNET": 95,

            "WEB_ATTACK": 65,

            "INFILTRATION": 100
        }

    # ==========================================
    # ATTACK NAME
    # ==========================================

    def get_attack_name(
        self,
        classification
    ):

        # Handle potential string mismatches or missing labels
        return self.attack_names.get(
            str(classification).strip(),
            "UNKNOWN"
        )

    # ==========================================
    # SEVERITY LEVEL
    # ==========================================

    def severity_level(
        self,
        score
    ):

        if score < 40:

            return "LOW"

        elif score < 70:

            return "MEDIUM"

        elif score < 90:

            return "HIGH"

        return "CRITICAL"

    # ==========================================
    # CALCULATE RISK
    # ==========================================

    def evaluate(
        self,
        result
    ):

        if not result["is_anomaly"]:

            return {

                "severity": "LOW",

                "risk_score": 0,

                "attack_type": "NORMAL"
            }

        attack_type = (
            self.get_attack_name(
                result[
                    "classification"
                ]
            )
        )

        # AI Contradiction Fallback Logic
        # If the Autoencoder screams Anomaly, but LightGBM thinks it's Benign, 
        # it means this is an Out-of-Distribution / Zero-Day attack!
        if attack_type == "BENIGN":
            attack_type = "ZERO_DAY_ANOMALY"
            base_score = 85  # Treat unknown massive anomalies as HIGH/CRITICAL risk
        else:
            base_score = (
                self.base_weights.get(
                    attack_type,
                    50
                )
            )

        confidence = (

            result[
                "confidence"
            ]
        )

        risk_score = (

            base_score *
            confidence

        )

        severity = (

            self.severity_level(
                risk_score
            )

        )

        return {

            "severity":
                severity,

            "risk_score":
                float(
                    risk_score
                ),

            "attack_type":
                attack_type
        }