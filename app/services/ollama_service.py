import httpx
import json
import logging
import re
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import LinkAnalysisResponse

logger = logging.getLogger(__name__)


class OllamaServiceError(Exception):
    """Raised when Ollama request fails."""


async def check_ollama_alive() -> bool:
    """Check if the local Ollama instance is online and reachable."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def analyze_with_ollama(website_data: dict, competitor_signals: dict | None = None) -> LinkAnalysisResponse:
    """
    Send prompt to local Ollama instance with format='json'
    and validate the structured output.
    """
    from app.services.llm_service import build_prompt, SYSTEM_PROMPT

    prompt = build_prompt(website_data, competitor_signals)
    full_prompt = f"{SYSTEM_PROMPT}\n\nUSER PROMPT:\n{prompt}"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "").strip()

            if not raw_response:
                raise OllamaServiceError("Ollama returned an empty response.")

            # Strip markdown fences if present
            cleaned = raw_response
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            result = LinkAnalysisResponse.model_validate_json(cleaned)
            result.website = website_data.get("url", result.website)
            return result

    except httpx.ConnectError as exc:
        raise OllamaServiceError(f"Ollama server not reachable at {OLLAMA_BASE_URL}") from exc
    except httpx.TimeoutException as exc:
        raise OllamaServiceError("Ollama local generation timed out.") from exc
    except Exception as exc:
        raise OllamaServiceError(f"Ollama generation failed: {str(exc)}") from exc
