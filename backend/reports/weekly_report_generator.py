"""
Weekly Report Generator
Builds the comprehensive A3-ENDS Weekly SOC Report PDF using Jinja2 and Weasyprint.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def generate_weekly_pdf_report(stats: dict, llm_summary: str, llm_recommendations: str, output_path: Path) -> Path:
    """
    Renders the weekly_report_template.html with the aggregated stats and LLM text,
    then saves it as a PDF using Weasyprint.
    """
    # Initialize Jinja2 environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("weekly_report_template.html")
    
    # Render HTML
    html_content = template.render(
        stats=stats,
        llm_summary=llm_summary,
        llm_recommendations=llm_recommendations
    )
    
    # Import inside to avoid dependency issues if not installed globally
    from weasyprint import HTML
    
    # Write to PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    HTML(string=html_content).write_pdf(
        str(output_path),
        presentational_hints=True
    )
        
    return output_path
