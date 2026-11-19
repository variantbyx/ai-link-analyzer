import logging
from app.schemas import LinkAnalysisResponse
from app.services.website_extractor import extract_website
from app.services.competitor_service import extract_competitor_signals
from app.services.llm_provider import generate_analysis_unified, ProviderQuotaExhaustedError
from app.services.llm_service import LLMServiceError

logger = logging.getLogger(__name__)


class AnalysisServiceError(Exception):
    """Raised when link analysis fails at any stage."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def process_link_analysis(url: str) -> LinkAnalysisResponse:
    """
    Complete orchestration pipeline:
    1. Validate URL & Fetch website content safely
    2. Extract metadata, text, headings, and JSON-LD schema
    3. Generate competitor research signals
    4. Execute Provider-Independent Intelligence Analysis
       (Cache -> Gemini Free Cloud -> Ollama Local -> Deterministic Offline Fallback)
    5. Validate and return LinkAnalysisResponse
    """
    # 1. Fetch & Extract
    try:
        website_data = await extract_website(url)
    except ValueError as exc:
        logger.warning(f"Validation or extraction error for {url}: {exc}")
        error_msg = str(exc)
        if "timed out" in error_msg.lower():
            raise AnalysisServiceError(f"Website request timed out: {error_msg}", status_code=504)
        if "not allowed" in error_msg.lower() or "ssrf" in error_msg.lower():
            raise AnalysisServiceError(f"Security restriction: {error_msg}", status_code=403)
        raise AnalysisServiceError(error_msg, status_code=400)
    except Exception as exc:
        logger.error(f"Unexpected extraction error for {url}: {exc}", exc_info=True)
        raise AnalysisServiceError(f"Failed to extract website content: {str(exc)}", status_code=502)

    # 2. Extract Competitor Signals
    try:
        competitor_signals = extract_competitor_signals(website_data)
    except Exception as exc:
        logger.warning(f"Error computing competitor signals: {exc}")
        competitor_signals = None

    # 3. Provider-Independent Analysis (with zero-budget cascade)
    try:
        result, provider_used = await generate_analysis_unified(website_data, competitor_signals)
        logger.info(f"Analysis completed for {url} using provider: '{provider_used}'")
        return result
    except ProviderQuotaExhaustedError as exc:
        logger.warning(f"Quota exhausted for {url}: {exc}")
        raise AnalysisServiceError(
            "Upstream AI provider daily quota / rate limit exhausted. Please try again later or use LLM_PROVIDER=offline.",
            status_code=429
        )
    except LLMServiceError as exc:
        err_msg = str(exc)
        logger.error(f"LLM analysis failed for {url}: {err_msg}")
        if "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower():
            raise AnalysisServiceError(
                "Upstream AI provider daily quota or rate limit exceeded. Please try again later.",
                status_code=429
            )
        raise AnalysisServiceError(err_msg, status_code=502)
    except Exception as exc:
        logger.error(f"Unexpected analysis failure for {url}: {exc}", exc_info=True)
        raise AnalysisServiceError("An unexpected error occurred during AI analysis.", status_code=500)
