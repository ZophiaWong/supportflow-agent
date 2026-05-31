from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


def load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def chat_completions_url() -> str:
    base_url = os.getenv("SUPPORTFLOW_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not base_url.endswith("/chat/completions"):
        base_url = f"{base_url}/chat/completions"
    return base_url


def main() -> int:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SUPPORTFLOW_LLM_API_KEY")
    if not api_key:
        print(
            "Missing LLM API key. Set OPENAI_API_KEY or SUPPORTFLOW_LLM_API_KEY in .env.",
            file=sys.stderr,
        )
        return 1

    payload = {
        "model": os.getenv("SUPPORTFLOW_LLM_MODEL", DEFAULT_MODEL),
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "你好"}],
            }
        ],
        "temperature": 0.9,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(chat_completions_url(), json=payload, headers=headers)
    print(response.text)
    return 0 if response.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
