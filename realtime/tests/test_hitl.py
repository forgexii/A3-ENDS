from realtime.hitl.hitl_manager import (
    HITLManager
)

manager = HITLManager()

sample = {

    "severity":
        "CRITICAL"
}

result = manager.process(
    sample
)

print(result)