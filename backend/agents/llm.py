"""One wrapper for text and vision calls to Claude. Every agent in this
package talks to the LLM through call_text()/call_vision() instead of the
Anthropic SDK directly, so model choice and error handling live in one place."""

import base64
import json

import anthropic

from config import LLM_API_KEY

MODEL = "claude-sonnet-4-5"

_client = None


def _get_client():
    global _client
    if _client is None:
        if not LLM_API_KEY:
            raise RuntimeError("LLM_API_KEY is not set in .env")
        _client = anthropic.Anthropic(api_key=LLM_API_KEY)
    return _client


def call_text(system: str, prompt: str, max_tokens: int = 1024) -> str:
    """Plain text completion. Returns the raw text response."""
    client = _get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def call_vision(system: str, prompt: str, image_bytes: bytes, media_type: str = "image/jpeg", max_tokens: int = 1024) -> str:
    """Vision completion: compares an image against a text prompt."""
    client = _get_client()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return response.content[0].text


def call_json(system: str, prompt: str, max_tokens: int = 1024) -> dict:
    """Text completion that asks for, and parses, a JSON object response."""
    text = call_text(system, prompt, max_tokens=max_tokens)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def call_json_vision(system: str, prompt: str, image_bytes: bytes, media_type: str = "image/jpeg", max_tokens: int = 1024) -> dict:
    """Vision completion that asks for, and parses, a JSON object response."""
    text = call_vision(system, prompt, image_bytes, media_type=media_type, max_tokens=max_tokens)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
