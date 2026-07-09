"""
OpenRouter Client
"""

import os
import requests

from backend.llm.prompt_templates import (
    build_incident_prompt
)


class OpenRouterClient:

    def __init__(
        self,
        api_key
    ):

        self.api_key = api_key

        self.url = (
            "https://openrouter.ai/api/v1/chat/completions"
        )

        self.model = os.getenv(
            "OPENROUTER_MODEL",
            "deepseek/deepseek-chat"
        )

    # ==========================================
    # ANALYZE DETECTION
    # ==========================================

    def analyze_detection(
        self,
        detection
    ):

        if not self.api_key:

            return {
                "error":
                    "OPENROUTER_API_KEY not configured"
            }

        prompt = (
            build_incident_prompt(
                detection
            )
        )

        payload = {

            "model":
                self.model,

            "messages": [

                {
                    "role":
                        "user",

                    "content":
                        prompt
                }

            ],

            "max_tokens":
                1000,

            "temperature":
                0.3
        }

        headers = {

            "Authorization":
                f"Bearer {self.api_key}",

            "Content-Type":
                "application/json"
        }

        try:

            print(
                f"Using model: {self.model}"
            )

            response = requests.post(

                self.url,

                json=payload,

                headers=headers,

                timeout=60
            )

            print(
                f"Status: {response.status_code}"
            )

            if response.status_code != 200:

                print(
                    response.text
                )

                return {

                    "error":
                        f"OpenRouter Error {response.status_code}",

                    "details":
                        response.text
                }

            data = response.json()

            return (

                data["choices"][0]
                ["message"]
                ["content"]

            )

        except Exception as e:

            return {

                "error":
                    str(e)
            }

    def generate_weekly_summary(self, stats: dict) -> str:
        if not self.api_key: return "LLM Summary not available (No API Key)"
        from backend.llm.prompt_templates import build_weekly_summary_prompt
        prompt = build_weekly_summary_prompt(stats)
        return self._send_prompt(prompt)

    def generate_weekly_recommendations(self, stats: dict) -> str:
        if not self.api_key: return "LLM Recommendations not available (No API Key)"
        from backend.llm.prompt_templates import build_weekly_recommendations_prompt
        prompt = build_weekly_recommendations_prompt(stats)
        return self._send_prompt(prompt)

    def _send_prompt(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(self.url, json=payload, headers=headers, timeout=60)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            return f"Error: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Error: {str(e)}"