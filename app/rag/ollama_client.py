import os

import requests


class OllamaClient:
    """
    Client for communicating with a local Ollama model.

    The Ollama endpoint can be configured through the
    TRACEAI_OLLAMA_URL environment variable.
    """

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        base_url: str | None = None,
        timeout: int = 180,
        max_tokens: int = 650,
    ):
        self.model = model
        self.base_url = (
            base_url
            or os.getenv(
                "TRACEAI_OLLAMA_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
    ) -> str:

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": self.max_tokens,
                    "top_p": 0.9,
                },
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        return data["response"]