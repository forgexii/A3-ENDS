"""
Risk Engine

Calculates threat severity and
risk scores from AI detections.
"""


class RiskEngine:

    def __init__(self):

        self.attack_names = {

            0: "BENIGN",

            1: "PORTSCAN",

            2: "DOS",

            3: "DDOS",

            4: "BRUTE_FORCE",

            5: "BOTNET",

            6: "WEB_ATTACK",

            7: "INFILTRATION"
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

        return self.attack_names.get(
            classification,
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