"""
LLM Report Generator
"""

import os

from dotenv import load_dotenv

from backend.llm.openrouter_client import (
    OpenRouterClient
)

load_dotenv()

client = OpenRouterClient(

    os.getenv(
        "OPENROUTER_API_KEY"
    )

)


# ==========================================
# GENERATE REPORT
# ==========================================

def generate_llm_report(
    detection
):

    return client.analyze_detection(
        detection
    )