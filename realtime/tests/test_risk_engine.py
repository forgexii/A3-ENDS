from realtime.risk.risk_engine import (
    RiskEngine
)


engine = RiskEngine()


sample = {

    "is_anomaly": True,

    "classification": 3,

    "confidence": 0.94
}


result = engine.evaluate(
    sample
)

print(result)