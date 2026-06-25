"""
Report Service

Coordinates forensic report
generation.
"""

from backend.reports.word_generator import (
    generate_word_report
)

from backend.reports.excel_generator import (
    generate_excel_report
)

from backend.reports.powerpoint_generator import (
    generate_powerpoint_report
)


class ReportService:

    @staticmethod
    def generate_report(

        report_type: str,

        detections: list

    ):

        if report_type == "word":

            return generate_word_report(
                detections
            )

        elif report_type == "excel":

            return generate_excel_report(
                detections
            )

        elif report_type == "powerpoint":

            return generate_powerpoint_report(
                detections
            )

        raise ValueError(
            "Unsupported report type"
        )