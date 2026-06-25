from realtime.response.response_engine import (
    ResponseEngine
)

engine = ResponseEngine()

sample = {

    "severity": "CRITICAL",

    "risk_score": 94.5,

    "attack_type": "DDOS",

    "action":
        "IMMEDIATE_RESPONSE",

    "source_ip":
        "192.168.1.10"
}

engine.execute(
    sample
)