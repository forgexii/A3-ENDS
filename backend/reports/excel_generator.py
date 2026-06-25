from pathlib import Path

import pandas as pd


def generate_excel_report(
    detections
):

    reports_dir = Path(
        "generated_reports"
    )

    reports_dir.mkdir(
        exist_ok=True
    )

    report_path = (

        reports_dir /

        "incident_summary.xlsx"
    )

    df = pd.DataFrame(
        detections
    )

    df.to_excel(

        report_path,

        index=False

    )

    return str(
        report_path
    )