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

def generate_weekly_llm_summary(stats: dict) -> str:
    return client.generate_weekly_summary(stats)

def generate_weekly_llm_recommendations(stats: dict) -> str:
    return client.generate_weekly_recommendations(stats)