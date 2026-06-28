from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Iterable
import urllib.error
import urllib.parse
import urllib.request

from app.config import GEMINI_MODEL_FALLBACKS


@dataclass
class GeminiGenerationResult:
    text: str
    model_name: str
    attempts: list[str] = field(default_factory=list)


def _extract_text_from_rest_response(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts") or []
    texts = [str(part.get("text", "")).strip() for part in parts if part.get("text")]
    return "\n".join(text for text in texts if text).strip()


def _generate_with_rest(*, api_key: str, model_name: str, prompt: str) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?"
        + urllib.parse.urlencode({"key": api_key})
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    return _extract_text_from_rest_response(data)


def _generate_with_google_genai(*, api_key: str, model_name: str, prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return (getattr(response, "text", "") or "").strip()


def generate_content_with_fallback(
    *,
    api_key: str,
    prompt: str,
    model_names: Iterable[str] = GEMINI_MODEL_FALLBACKS,
) -> GeminiGenerationResult:
    """Generate Gemini content with model fallback and empty-response control."""

    clean_key = api_key.strip()
    if not clean_key:
        raise ValueError("Gemini API key is empty.")

    attempts: list[str] = []
    last_error = ""
    use_rest_fallback = False

    for model_name in model_names:
        try:
            if use_rest_fallback:
                text = _generate_with_rest(api_key=clean_key, model_name=model_name, prompt=prompt)
                channel = "rest"
            else:
                try:
                    text = _generate_with_google_genai(api_key=clean_key, model_name=model_name, prompt=prompt)
                    channel = "google-genai"
                except ImportError:
                    use_rest_fallback = True
                    text = _generate_with_rest(api_key=clean_key, model_name=model_name, prompt=prompt)
                    channel = "rest"
            if text:
                attempts.append(f"{model_name}: ok via {channel}")
                return GeminiGenerationResult(text=text, model_name=model_name, attempts=attempts)
            attempts.append(f"{model_name}: empty response via {channel}")
            last_error = "Gemini API 回傳空文字。"
        except Exception as exc:
            last_error = str(exc)
            attempts.append(f"{model_name}: {type(exc).__name__}: {last_error}")

    attempt_text = "\n".join(f"- {attempt}" for attempt in attempts)
    raise RuntimeError(f"Gemini API 所有模型皆無法產生有效文字。\n{attempt_text}\n最後錯誤：{last_error}")
