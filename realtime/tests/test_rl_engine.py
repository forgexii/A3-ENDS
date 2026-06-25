from realtime.rl.policy_engine import (
    PolicyEngine
)

engine = PolicyEngine()

result = engine.decide(

    {
        "severity": "HIGH",

        "drift_detected": False
    }

)

print(result)