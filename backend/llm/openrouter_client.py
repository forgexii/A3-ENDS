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