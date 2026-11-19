from urllib.parse import urlsplit


def extract_competitor_signals(website_data: dict) -> dict:
    """
    Extract clues about business industry, market positioning,
    and external references to assist competitor identification.
    """
    title = website_data.get("title", "")
    description = website_data.get("description", "")
    headings = website_data.get("headings", [])
    links = website_data.get("links", [])
    json_ld = website_data.get("json_ld", [])

    # Identify external domains referenced on the page
    current_host = urlsplit(website_data.get("url", "")).netloc.lower()
    external_domains = []

    for link in links:
        link_url = link.get("url", "")
        parsed = urlsplit(link_url)
        host = parsed.netloc.lower()
        if host and host != current_host and not any(social in host for social in ["facebook", "twitter", "x.com", "instagram", "linkedin", "youtube", "tiktok", "pinterest", "google", "apple"]):
            if host not in external_domains:
                external_domains.append(host)

    # Collect entity types from JSON-LD
    schema_types = [item.get("type") for item in json_ld if item.get("type")]

    return {
        "primary_signals": {
            "title": title,
            "description": description,
            "top_headings": headings[:10],
            "schema_types": schema_types
        },
        "external_references": external_domains[:5],
        "research_guidelines": (
            "Identify at least 3 direct or strong competitors in the same market or industry segment. "
            "For each competitor, accurately label source_type as: "
            "'model_knowledge' for established industry players known from general model knowledge, "
            "or 'inferred' for niche/regional market competitors derived from category context."
        )
    }
