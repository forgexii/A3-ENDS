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

def build_weekly_summary_prompt(weekly_stats: dict) -> str:
    return f"""
You are a senior SOC analyst reporting to the CISO. 
Write a one-paragraph Executive Summary for the Weekly SOC Report based on these metrics:

Total Flows: {weekly_stats['traffic']['total_flows']}
Confirmed Attacks: {weekly_stats['traffic']['confirmed_attacks']}
False Positives: {weekly_stats['traffic']['false_positives']}
Severity Breakdown: {weekly_stats['severity_distribution']}
Top Attack Types: {weekly_stats['attack_overview']}

Keep it concise, professional, and do not use markdown formatting (like **). Summarize the threat landscape and the system's automated responses.
"""

def build_weekly_recommendations_prompt(weekly_stats: dict) -> str:
    return f"""
You are a senior SOC analyst reporting to the CISO.
Based on the following weekly network metrics, provide 3 actionable, highly professional security recommendations in a single short paragraph.

Confirmed Attacks: {weekly_stats['traffic']['confirmed_attacks']}
Top Attack Types: {weekly_stats['attack_overview']}
Top Targeted Ports/Protocols in IOCs: {[i.get('port') for i in weekly_stats['iocs']]}

Do not use markdown lists or bolding. Write it as a flowing paragraph recommending firewall tuning, MFA, or architectural changes based on the predominant attacks seen.
"""