"""
Prompt Templates
"""


def build_incident_prompt(
    detection
):

    return f"""
You are a senior SOC analyst.

Analyze the following intrusion
detection event.

Attack Type:
{detection.get("attack_type")}

Severity:
{detection.get("severity")}

Risk Score:
{detection.get("risk_score")}

Confidence:
{detection.get("confidence")}

Generate:

1. Executive Summary
2. Threat Analysis
3. Potential Impact
4. Recommended Actions

Keep the response professional.
"""