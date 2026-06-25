from realtime.drift.adwin_engine import (
    ADWINEngine
)

adwin = ADWINEngine()

print(
    "\nTesting ADWIN..."
)

for i in range(100):

    result = adwin.update(
        0.001
    )

for i in range(100):

    result = adwin.update(
        5.0
    )

print(result)