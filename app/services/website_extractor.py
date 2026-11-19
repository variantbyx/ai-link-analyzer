import asyncio
import json
import re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
import httpx

from app.utils.validators import validate_url


MAX_HTML_SIZE = 2 * 1024 * 1024  # 2MB
MAX_CONTENT_LENGTH = 15000
MAX_REDIRECTS = 5


async def fetch_html(url: str) -> tuple[str, str]:
    """
    Fetch HTML from a website with security and reliability safeguards:
    - SSRF validation via validate_url
    - Manual redirect following to validate redirect targets
    - Size-limited streaming download
    - Custom desktop browser User-Agent
    """
    current_url = await validate_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    timeout = httpx.Timeout(20.0, connect=15.0)

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False
        ) as client:

            for attempt in range(MAX_REDIRECTS + 1):
                async with client.stream(
                    "GET",
                    current_url,
                    headers=headers
                ) as response:

                    # Handle redirects manually to re-validate destination IP
                    if response.is_redirect:
                        if attempt == MAX_REDIRECTS:
                            raise ValueError("Too many redirects.")

                        location = response.headers.get("location")
                        if not location:
                            raise ValueError("Invalid redirect response.")

                        next_url = urljoin(current_url, location)
                        current_url = await validate_url(next_url)
                        continue

                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "").lower()
                    if not (
                        "text/html" in content_type
                        or "application/xhtml+xml" in content_type
                    ):
                        raise ValueError("The URL does not return an HTML page.")

                    # Check declared content-length header
                    content_length = response.headers.get("content-length")
                    if content_length:
                        try:
                            if int(content_length) > MAX_HTML_SIZE:
                                raise ValueError("Website HTML is too large.")
                        except (ValueError, TypeError):
                            pass

                    # Stream bytes and enforce MAX_HTML_SIZE
                    chunks = []
                    total_size = 0

                    async for chunk in response.aiter_bytes():
                        total_size += len(chunk)
                        if total_size > MAX_HTML_SIZE:
                            raise ValueError("Website HTML is too large.")
                        chunks.append(chunk)

                    html_bytes = b"".join(chunks)

                    encoding = response.encoding or "utf-8"
                    try:
                        html = html_bytes.decode(encoding, errors="replace")
                    except (LookupError, TypeError):
                        html = html_bytes.decode("utf-8", errors="replace")

                    return html, current_url

        raise ValueError("Unable to fetch website.")

    except httpx.TimeoutException:
        raise ValueError(f"Request timed out while connecting to {url}.")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Website returned HTTP error {e.response.status_code} ({e.response.reason_phrase}).")
    except httpx.RequestError as e:
        raise ValueError(f"Failed to connect to website: {str(e)}")


def extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    """
    Extract and parse Schema.org JSON-LD scripts.
    Extracts Organization, WebSite, Corporation, LocalBusiness, and Product entities.
    """
    structured_data = []

    for tag in soup.find_all("script", type="application/ld+json"):
        raw_text = tag.string or tag.get_text()
        if not raw_text:
            continue

        try:
            data = json.loads(raw_text.strip())
            items = data if isinstance(data, list) else [data]

            for item in items:
                if not isinstance(item, dict):
                    continue

                entity_type = item.get("@type", "")
                if isinstance(entity_type, list):
                    entity_type = ", ".join(entity_type)

                # Capture high-value schema objects
                extracted_item = {
                    "type": entity_type,
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "url": item.get("url"),
                    "sameAs": item.get("sameAs"),
                    "keywords": item.get("keywords")
                }
                # Clean out None values
                cleaned = {k: v for k, v in extracted_item.items() if v}
                if cleaned:
                    structured_data.append(cleaned)

        except (json.JSONDecodeError, TypeError):
            continue

    return structured_data[:5]


def extract_content(html: str, url: str) -> dict:
    """
    Parse HTML and extract comprehensive business context:
    title, metadata, Open Graph data, Schema.org JSON-LD,
    structured headings, body text, and organized links.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Page Title
    title = (
        soup.title.get_text(strip=True)
        if soup.title else ""
    )

    # 2. Meta Description
    description_tag = soup.find(
        "meta",
        attrs={"name": re.compile(r"^description$", re.IGNORECASE)}
    )
    description = ""
    if description_tag and description_tag.get("content"):
        description = str(description_tag.get("content", "")).strip()

    # 3. Open Graph & Twitter Metadata
    og_data = {}
    for prop in ["og:title", "og:description", "og:site_name", "og:type", "twitter:description"]:
        meta_tag = soup.find(
            "meta",
            attrs={"property": re.compile(f"^{re.escape(prop)}$", re.IGNORECASE)}
        ) or soup.find(
            "meta",
            attrs={"name": re.compile(f"^{re.escape(prop)}$", re.IGNORECASE)}
        )
        if meta_tag and meta_tag.get("content"):
            og_data[prop] = str(meta_tag.get("content", "")).strip()

    # Fallback to OG description if standard description is empty
    if not description:
        description = og_data.get("og:description") or og_data.get("twitter:description") or ""

    # Meta Keywords
    keywords_tag = soup.find(
        "meta",
        attrs={"name": re.compile(r"^keywords$", re.IGNORECASE)}
    )
    meta_keywords = ""
    if keywords_tag and keywords_tag.get("content"):
        meta_keywords = str(keywords_tag.get("content", "")).strip()

    # 4. Structured Data (Schema.org JSON-LD)
    json_ld_data = extract_json_ld(soup)

    # 5. Extract Links BEFORE Decomposing Navigation
    links = []
    seen_urls = set()

    for tag in soup.find_all("a", href=True):
        href = tag.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute_url = urljoin(url, href)
        parsed = urlsplit(absolute_url)

        if parsed.scheme not in ("http", "https"):
            continue

        link_text = tag.get_text(" ", strip=True)
        # Avoid generic noise labels
        if not link_text or link_text.lower() in ("skip to content", "privacy policy", "terms of service"):
            continue

        if absolute_url not in seen_urls:
            seen_urls.add(absolute_url)
            links.append({
                "text": link_text[:120],
                "url": absolute_url
            })

        if len(links) >= 35:
            break

    # 6. Extract Button Actions / Interactive Features
    button_actions = []
    for btn in soup.find_all("button"):
        btn_text = btn.get_text(" ", strip=True)
        if btn_text and 2 < len(btn_text) < 80 and btn_text not in button_actions:
            button_actions.append(btn_text)

    # 7. Extract Headings Hierarchy
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(" ", strip=True)
        if text and len(text) > 2 and text not in headings:
            headings.append(text)

    # 8. Clean and Extract Readable Body Content
    for element in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "nav",
        "footer"
    ]):
        element.decompose()

    # Prefer semantic main containers with substantive text content
    candidates = [soup.find("main"), soup.find("article"), soup.body, soup]
    raw_content = ""
    for container in candidates:
        if container:
            text = container.get_text(separator=" ", strip=True)
            if len(text) >= 150:
                raw_content = text
                break
            elif not raw_content and text:
                raw_content = text

    content = " ".join(raw_content.split())
    content = content[:MAX_CONTENT_LENGTH]

    # Detect if content is suspiciously short
    is_sparse = len(content) < 150

    return {
        "url": url,
        "title": title,
        "description": description,
        "meta_keywords": meta_keywords,
        "og_data": og_data,
        "json_ld": json_ld_data,
        "headings": headings[:40],
        "button_actions": button_actions[:15],
        "content": content,
        "links": links,
        "is_sparse_content": is_sparse
    }


async def extract_website(url: str) -> dict:
    """
    Main entry point: fetches HTML and extracts structured website data.
    """
    html, final_url = await fetch_html(url)
    website_data = extract_content(html, final_url)
    return website_data
