from urllib.parse import urlsplit, urlunsplit
import logging
from app.schemas import LinkAnalysisResponse

logger = logging.getLogger(__name__)

# In-memory analysis cache
_CACHE: dict[str, LinkAnalysisResponse] = {}


def normalize_cache_url(url: str) -> str:
    """
    Normalize URLs for consistent cache lookups:
    - Lowercase scheme and domain
    - Strip trailing slashes, default ports, and tracking query params
    """
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove standard ports if explicitly specified
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path.rstrip("/")
    if not path:
        path = "/"

    # Reconstruct normalized URL without ephemeral fragments
    return urlunsplit((scheme, netloc, path, "", ""))


def get_cached_analysis(url: str) -> LinkAnalysisResponse | None:
    """Retrieve cached analysis if available."""
    key = normalize_cache_url(url)
    if key in _CACHE:
        logger.info(f"Cache HIT for {key}")
        return _CACHE[key]
    return None


def set_cached_analysis(url: str, response: LinkAnalysisResponse) -> None:
    """Store analysis in cache."""
    key = normalize_cache_url(url)
    _CACHE[key] = response
    logger.info(f"Cached analysis for {key}")


def clear_cache() -> None:
    """Clear all cached entries."""
    _CACHE.clear()
