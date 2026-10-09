"""Minimal Responses API client (stdlib only).

Configure via environment variables:
  OPENAI_API_KEY   - required, API key for the endpoint
  OPENAI_BASE_URL  - optional, defaults to https://api.openai.com/v1
                     (any OpenAI-compatible Responses API endpoint works)
"""
import json
import os
import urllib.request

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class ResponsesClient:
    def __init__(self, api_key=None, base_url=None, timeout=900):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL")
                         or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise SystemExit("Set OPENAI_API_KEY (and optionally OPENAI_BASE_URL)")

    def create(self, body):
        req = urllib.request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.load(r)
