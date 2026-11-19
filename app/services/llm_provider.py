import logging
from app.config import LLM_PROVIDER, GEMINI_API_KEY, ENABLE_CACHE
from app.schemas import LinkAnalysisResponse
from app.services.cache_service import get_cached_analysis, set_cached_analysis
from app.services.offline_analyzer import generate_offline_analysis
from app.services.ollama_service import analyze_with_ollama, check_ollama_alive, OllamaServiceError
from app.services.llm_service import analyze_website, LLMServiceError, LLMQuotaExhaustedError

logger = logging.getLogger(__name__)


class ProviderQuotaExhaustedError(Exception):
    """Raised specifically when Gemini rate limits or quota is fully exhausted."""


async def generate_analysis_unified(
    website_data: dict,
    competitor_signals: dict | None = None
) -> tuple[LinkAnalysisResponse, str]:
    """
    Provider-independent intelligence dispatcher:
    1. Checks URL cache first to preserve quota.
    2. Routes to selected provider or executes resilient auto-fallback:
       Gemini (Cloud Free) -> Ollama (Local Free) -> Offline Engine (Deterministic Rules).
    3. Caches successful result.
    Returns: (LinkAnalysisResponse, provider_name_used)
    """
    url = website_data.get("url", "")

    # 1. Check cache first
    if ENABLE_CACHE:
        cached = get_cached_analysis(url)
        if cached:
            logger.info(f"Returning cached analysis for {url}")
            return cached, "cache"

    provider = (LLM_PROVIDER or "auto").lower()

    # 2. Direct Provider Selection
    if provider == "offline":
        result = generate_offline_analysis(website_data)
        if ENABLE_CACHE:
            set_cached_analysis(url, result)
        return result, "offline_engine"

    if provider == "ollama":
        result = await analyze_with_ollama(website_data, competitor_signals)
        if ENABLE_CACHE:
            set_cached_analysis(url, result)
        return result, "ollama"

    if provider == "gemini":
        if not GEMINI_API_KEY:
            raise LLMServiceError("GEMINI_API_KEY is missing. Cannot use provider 'gemini'.")
        result = await analyze_website(website_data, competitor_signals)
        if ENABLE_CACHE:
            set_cached_analysis(url, result)
        return result, "gemini"

    # 3. Auto Mode (Resilient Zero-Budget Cascade)
    # A. Try Gemini if API key is configured
    if GEMINI_API_KEY and len(GEMINI_API_KEY.strip()) > 5:
        try:
            logger.info("Auto Mode: Attempting primary cloud provider (Gemini)...")
            result = await analyze_website(website_data, competitor_signals)
            if ENABLE_CACHE:
                set_cached_analysis(url, result)
            return result, "gemini"
        except LLMQuotaExhaustedError as exc:
            logger.warning(f"Auto Mode: Gemini daily quota exhausted. Cascading immediately to fallback: {exc}")
        except LLMServiceError as exc:
            err_msg = str(exc)
            logger.warning(f"Auto Mode: Gemini failed ({err_msg}). Falling back...")
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                logger.info("Gemini quota exhausted. Switching to zero-budget fallback.")

    # B. Try Local Ollama if online
    if await check_ollama_alive():
        try:
            logger.info("Auto Mode: Attempting local AI provider (Ollama)...")
            result = await analyze_with_ollama(website_data, competitor_signals)
            if ENABLE_CACHE:
                set_cached_analysis(url, result)
            return result, "ollama"
        except OllamaServiceError as exc:
            logger.warning(f"Auto Mode: Ollama failed ({exc}). Falling back to offline engine...")

    # C. Graceful Fallback: Deterministic Offline Rule-Based Engine
    logger.info("Auto Mode: Generating structured analysis using Deterministic Offline Engine (Zero Cost)...")
    result = generate_offline_analysis(website_data)
    if ENABLE_CACHE:
        set_cached_analysis(url, result)
    return result, "offline_engine"
