"""
HTML Report Generator
Builds the A3-ENDS forensic HTML report using Jinja2.
"""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

def generate_html_report(report_data: Dict[str, Any], output_path: Path) -> Path:
    """
    Renders the report_template.html with the provided report data.
    """
    
    # Process SHAP features for the bar chart
    shap: dict = report_data.get("shap_explanation") or {}
    sorted_shap = sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True) if shap else []
    
    max_abs = max((abs(v) for _, v in sorted_shap), default=1.0)
    
    shap_features = []
    for feat, val in sorted_shap[:6]:
        direction = "positive" if val >= 0 else "negative"
        width = min(100, max(2, (abs(val) / max_abs) * 100))
        shap_features.append({
            "name": feat,
            "value": f"{val:+.4f}",
            "direction": direction,
            "width": width
        })
    
    from markdown_it import MarkdownIt
    md = MarkdownIt()
    
    raw_llm = report_data.get("llm_analysis", "No AI analysis available.")
    # Convert LLM Markdown output to valid HTML
    html_llm_analysis = md.render(raw_llm)
    
    # Render with Jinja2
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("report_template.html")
    
    html_content = template.render(
        report_id=report_data.get("report_id", "Unknown"),
        timestamp=report_data.get("timestamp", "Unknown"),
        severity=report_data.get("severity", "UNKNOWN"),
        attack_type=report_data.get("attack_type", "Unknown"),
        confidence=report_data.get("confidence", "0.0"),
        llm_analysis=html_llm_analysis,
        source_ip=report_data.get("source_ip", "N/A"),
        dest_ip=report_data.get("dest_ip", "N/A"),
        protocol=report_data.get("protocol", "N/A"),
        shap_features=shap_features,
        anomaly_score=report_data.get("anomaly_score", "N/A"),
        response_actions=report_data.get("response_actions", []),
        risk_score=report_data.get("risk_score", "0"),
        analyst_decision=report_data.get("analyst_decision", "Pending")
    )
    
    from weasyprint import HTML, CSS
    
    # Write to PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    HTML(string=html_content).write_pdf(
        str(output_path),
        presentational_hints=True
    )
        
    return output_path
