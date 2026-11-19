from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from collections import OrderedDict
import logging
import time
from typing import Tuple

from app.schemas import LinkAnalysisResponse
from app.config import CACHE_TTL_SECONDS, CACHE_MAX_SIZE

logger = logging.getLogger(__name__)

# Tracking query parameters that do not alter page business content
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "mc_eid", "_ga", "yclid", "dclid"
}

# In-memory LRU cache storing: key -> (LinkAnalysisResponse, creation_timestamp)
_CACHE: OrderedDict[str, Tuple[LinkAnalysisResponse, float]] = OrderedDict()


def normalize_cache_url(url: str) -> str:
    """
    Normalize URLs for consistent, collision-free cache lookups:
    - Lowercase scheme and domain
    - Strip standard web ports (80/443)
    - Preserve distinct resource paths (normalize trailing slash)
    - Strip ephemeral tracking query params (utm_*, fbclid, gclid)
    - Sort and retain legitimate business query parameters (?id=1 vs ?id=2)
    - Strip in-page fragment identifiers (#section)
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

    # Strip marketing/tracking params, preserve and sort functional query params
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = [
        (k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS
    ]
    filtered_params.sort(key=lambda item: (item[0], item[1]))
    clean_query = urlencode(filtered_params)

    return urlunsplit((scheme, netloc, path, clean_query, ""))


def get_cached_analysis(url: str, requested_url: str | None = None) -> LinkAnalysisResponse | None:
    """
    Retrieve cached analysis if available and not expired.
    Ensures:
    - Expiration check (TTL).
    - Returns a deep copy so internal cache state cannot be corrupted.
    - Preserves the caller's requested website URL in the response.
    """
    key = normalize_cache_url(url)
    entry = _CACHE.get(key)

    if not entry:
        return None

    response, timestamp = entry

    # Verify cache TTL
    now = time.time()
    if (now - timestamp) > CACHE_TTL_SECONDS:
        logger.info(f"Cache EXPIRED for {key} (age: {int(now - timestamp)}s > {CACHE_TTL_SECONDS}s)")
        del _CACHE[key]
        return None

    # Move accessed entry to end for LRU order
    _CACHE.move_to_end(key)
    logger.info(f"Cache HIT for {key}")

    # Return deep copy with requested URL preserved
    target_url = requested_url or url
    cached_copy = response.model_copy(deep=True, update={"website": target_url})
    return cached_copy


def set_cached_analysis(url: str, response: LinkAnalysisResponse) -> None:
    """
    Store successful analysis in cache.
    Guarantees:
    - Failed or invalid analyses are never cached.
    - Cache enforces LRU eviction when CACHE_MAX_SIZE is reached.
    """
    if not response or not getattr(response, "success", False):
        logger.warning(f"Refusing to cache unsuccessful or invalid response for {url}")
        return

    key = normalize_cache_url(url)

    # Enforce LRU capacity limit
    if len(_CACHE) >= CACHE_MAX_SIZE and key not in _CACHE:
        oldest_key, _ = _CACHE.popitem(last=False)
        logger.debug(f"Evicted oldest cache entry: {oldest_key}")

    # Store a deep copy with current timestamp
    _CACHE[key] = (response.model_copy(deep=True), time.time())
    _CACHE.move_to_end(key)
    logger.info(f"Cached analysis for {key}")


def clear_cache() -> None:
    """Clear all cached entries."""
    _CACHE.clear()
