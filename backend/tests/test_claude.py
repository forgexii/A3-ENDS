from backend.llm.report_generator import (
    generate_llm_report
)

detection = {

    "attack_type":
        "PORTSCAN",

    "severity":
        "HIGH",

    "risk_score":
        0.91,

    "confidence":
        0.94
}

report = generate_llm_report(
    detection
)

print("\nREPORT")
print("=" * 50)
print(report)