from urllib.parse import urlsplit
import re

from app.schemas import (
    LinkAnalysisResponse,
    Brand,
    Analysis,
    CompetitorAnalysis,
    Competitor,
    TargetSearchQuery,
    SEOImprovements,
    Service,
    TargetAudience,
    AudienceProfile
)


# Category-specific competitor profiles
CATEGORY_COMPETITORS = {
    "AI & Software": [
        Competitor(
            name="Google Gemini",
            website="https://gemini.google.com/",
            overview="Google's multimodal generative AI platform integrated with Google Workspace and search.",
            strengths=["Deep Google ecosystem integration", "Multimodal comprehension", "Broad multilingual reach"],
            weaknesses_or_gaps=["Ecosystem lock-in", "Variable response styles depending on integration"],
            source_type="model_knowledge"
        ),
        Competitor(
            name="Microsoft Copilot",
            website="https://copilot.microsoft.com/",
            overview="Enterprise and consumer AI assistant embedded across Microsoft 365, Windows, and Edge.",
            strengths=["Direct Office 365 workflow integration", "Enterprise compliance", "Commercial data protection"],
            weaknesses_or_gaps=["Requires Microsoft infrastructure for full utility", "Less developer customization"],
            source_type="model_knowledge"
        ),
        Competitor(
            name="Anthropic Claude",
            website="https://www.anthropic.com/",
            overview="AI assistant designed with safety-first Constitutional AI, known for long-form reasoning.",
            strengths=["Exceptional long-context comprehension", "Thoughtful and nuanced prose", "Strong code generation"],
            weaknesses_or_gaps=["Smaller ecosystem integration footprint than Big Tech incumbents"],
            source_type="model_knowledge"
        )
    ],
    "Retail & E-commerce": [
        Competitor(
            name="Amazon",
            website="https://www.amazon.com/",
            overview="Global retail marketplace and logistics network offering fast fulfillment and vast catalog selection.",
            strengths=["Industry-leading logistics", "Prime subscription loyalty", "Vast third-party catalog"],
            weaknesses_or_gaps=["Inconsistent third-party vendor quality", "Less curated brand presence"],
            source_type="model_knowledge"
        ),
        Competitor(
            name="Target",
            website="https://www.target.com/",
            overview="National general merchandise retailer known for curated private labels and omnichannel fulfillment.",
            strengths=["Strong design-forward private brands", "Omnichannel Drive Up pickup", "Loyal customer base"],
            weaknesses_or_gaps=["Smaller global and digital footprint compared to mega-retailers", "Higher price on select staples"],
            source_type="model_knowledge"
        ),
        Competitor(
            name="Costco Wholesale",
            website="https://www.costco.com/",
            overview="Membership warehouse club offering bulk goods, groceries, and services at high unit value.",
            strengths=["High customer loyalty", "Low markup unit economics", "Trusted Kirkland Signature brand"],
            weaknesses_or_gaps=["Membership barrier to purchase", "Limited item selection compared to open catalogs"],
            source_type="model_knowledge"
        )
    ],
    "Default": [
        Competitor(
            name="Industry Peer A",
            website=None,
            overview="Established market competitor providing comparable industry solutions.",
            strengths=["Market seniority", "Broad brand awareness"],
            weaknesses_or_gaps=["Slower innovation cycles", "Higher switching costs"],
            source_type="inferred"
        ),
        Competitor(
            name="Industry Peer B",
            website=None,
            overview="Regional or specialized alternative operating within the same market vertical.",
            strengths=["Niche specialization", "Agile customer support"],
            weaknesses_or_gaps=["Limited regional footprint", "Smaller resource base"],
            source_type="inferred"
        ),
        Competitor(
            name="Industry Peer C",
            website=None,
            overview="Emerging digital provider offering alternative pricing and modern tooling.",
            strengths=["Modern user experience", "Competitive introductory pricing"],
            weaknesses_or_gaps=["Unproven long-term scale", "Narrower feature depth"],
            source_type="inferred"
        )
    ]
}


def detect_brand_name(website_data: dict) -> str:
    """Extract credible brand name from structured data, title, or domain."""
    # 1. Check JSON-LD
    for item in website_data.get("json_ld", []):
        if item.get("name") and len(item["name"]) < 40:
            return item["name"].strip()

    # 2. Check Open Graph site name
    og_name = website_data.get("og_data", {}).get("og:site_name")
    if og_name and len(og_name) < 40:
        return og_name.strip()

    # 3. Check Title delimiter
    title = website_data.get("title", "")
    for delimiter in ["|", "-", ":", "•", "–"]:
        if delimiter in title:
            candidate = title.split(delimiter)[0].strip()
            if 1 < len(candidate) < 30:
                return candidate

    # 4. Fallback to domain root
    netloc = urlsplit(website_data.get("url", "")).netloc.lower()
    netloc = re.sub(r"^www\.", "", netloc)
    domain_root = netloc.split(".")[0].capitalize()
    return domain_root or "Brand"


def detect_category(website_data: dict) -> str:
    """Detect business category based on keywords in title, description, and headings."""
    text_corpus = (
        website_data.get("title", "") + " " +
        website_data.get("description", "") + " " +
        " ".join(website_data.get("headings", []))
    ).lower()

    if any(k in text_corpus for k in ["ai", "chatbot", "generative", "model", "code", "software", "api"]):
        return "AI & Software"
    if any(k in text_corpus for k in ["shop", "store", "price", "deals", "groceries", "retail", "cart", "shipping"]):
        return "Retail & E-commerce"
    if any(k in text_corpus for k in ["cloud", "server", "hosting", "devops", "kubernetes"]):
        return "Cloud & Technology Services"
    if any(k in text_corpus for k in ["consulting", "agency", "marketing", "digital solutions"]):
        return "Digital & Professional Services"

    return "Business & Digital Services"


def generate_offline_analysis(website_data: dict) -> LinkAnalysisResponse:
    """
    Generate a 100% free, deterministic, schema-compliant analysis
    using rule-based semantic parsing of the extracted website content.
    Requires zero external API calls or tokens.
    """
    url = website_data.get("url", "https://example.com")
    brand_name = detect_brand_name(website_data)
    category = detect_category(website_data)
    title = website_data.get("title") or f"{brand_name} Official Website"
    description = website_data.get("description") or f"Official online platform for {brand_name} providing specialized {category} solutions."
    headings = website_data.get("headings", [])
    button_actions = website_data.get("button_actions", [])

    # Competitors
    competitors = CATEGORY_COMPETITORS.get(category, CATEGORY_COMPETITORS["Default"])

    # Extract 5 Top Services / Capabilities directly from headings and buttons
    services: list[Service] = []
    seen_names = set()

    # Collect high-value candidate phrases
    candidates = []
    for h in headings:
        if 4 < len(h) < 60 and not any(w in h.lower() for w in ["welcome", "sign in", "log in", "cookie", "privacy"]):
            candidates.append((h, "website_evidence", h))

    for btn in button_actions:
        if 4 < len(btn) < 40 and not any(w in btn.lower() for w in ["sign in", "log in", "continue", "submit"]):
            candidates.append((btn, "website_evidence", btn))

    # Add candidates to services
    for name, id_type, snippet in candidates:
        clean_name = name.strip()
        if clean_name.lower() not in seen_names:
            seen_names.add(clean_name.lower())
            services.append(Service(
                name=clean_name,
                description=f"Core offering of {brand_name} focused on delivering {clean_name.lower()}.",
                target_industry=category,
                target_customer="Consumers and business clients seeking reliable solutions",
                main_benefit=f"Provides immediate access to {clean_name.lower()}.",
                identification_type="website_evidence",
                evidence=snippet
            ))
        if len(services) >= 5:
            break

    # If fewer than 5, supplement with well-grounded category inferences
    default_offerings = [
        ("Core Digital Platform", "Centralized digital interface for accessing all product features and resources."),
        ("Customer Account Management", "Secure user account infrastructure for profiles, history, and preferences."),
        ("Support & Knowledge Resources", "Assistance, documentation, and user guidance for optimal product usage."),
        ("Mobile & Web Access", "Cross-device accessibility for desktop and mobile environments."),
        ("Enterprise & Team Solutions", "Scalable collaboration features designed for professional workflows.")
    ]

    for name, desc in default_offerings:
        if len(services) >= 5:
            break
        if name.lower() not in seen_names:
            seen_names.add(name.lower())
            services.append(Service(
                name=name,
                description=desc,
                target_industry=category,
                target_customer="Individuals and teams using the platform",
                main_benefit=f"Enhances operational efficiency with {name.lower()}.",
                identification_type="inferred_recommendation",
                evidence=None
            ))

    # Search Queries
    search_queries = [
        TargetSearchQuery(
            query=f"{brand_name} official website",
            platforms=["Google"],
            intent="Navigational",
            business_relevance=f"Primary brand discovery query for users looking directly for {brand_name}.",
            target_audience="Existing users and direct searchers"
        ),
        TargetSearchQuery(
            query=f"best {category.lower()} tools",
            platforms=["Google", "LinkedIn"],
            intent="Commercial Investigation",
            business_relevance=f"Positions {brand_name} among leading solutions in the {category} sector.",
            target_audience="Decision makers and prospective buyers"
        ),
        TargetSearchQuery(
            query=f"{brand_name} features and pricing",
            platforms=["Google", "X"],
            intent="Commercial Investigation",
            business_relevance="Captures high-intent prospects comparing product tiers and subscription value.",
            target_audience="Active evaluators comparing competitive pricing"
        ),
        TargetSearchQuery(
            query=f"{brand_name} customer reviews",
            platforms=["Google", "Facebook"],
            intent="Informational",
            business_relevance="Attracts consumers seeking social proof and user feedback before purchasing.",
            target_audience="Prospective buyers conducting due diligence"
        ),
        TargetSearchQuery(
            query=f"how to use {brand_name} for business",
            platforms=["LinkedIn", "YouTube" if "YouTube" in TargetSearchQuery.model_fields["platforms"].annotation.__args__ else "Google"],
            intent="Informational / Practical",
            business_relevance="Demonstrates business use-cases and drives professional user acquisition.",
            target_audience="Professionals, operators, and team managers"
        )
    ]

    # Primary Keyword derivation
    primary_kw = f"{brand_name} {category.split('&')[0].strip()}"

    return LinkAnalysisResponse(
        success=True,
        website=url,
        brand=Brand(
            name=brand_name,
            category=category,
            summary=description
        ),
        analysis=Analysis(
            competitor_analysis=CompetitorAnalysis(
                brand_overview=f"{brand_name} operates in the {category} market, providing digital access via {url}. The platform focuses on user convenience, accessible tooling, and digital delivery.",
                competitors=competitors,
                strengths=[
                    f"Established digital presence at {url}",
                    f"Specialized feature set tailored to {category}",
                    "Direct consumer access with cross-platform compatibility"
                ],
                opportunities=[
                    "Expand localized marketing to capture international search demand",
                    "Enhance user onboarding workflows to improve retention",
                    "Develop strategic partnerships to strengthen domain authority"
                ],
                methodology_note="Competitor comparisons reflect model-generated market observations and general industry knowledge. Specific market share, financial performance, or detailed feature parity would require empirical, real-time data from market research firms."
            ),
            target_search_queries=search_queries,
            seo_improvements=SEOImprovements(
                primary_keyword=primary_kw,
                secondary_keywords=[brand_name, category, f"{brand_name} online", f"{brand_name} platform"],
                long_tail_keywords=[
                    f"how to get started with {brand_name}",
                    f"best {category.lower()} alternatives to {brand_name}",
                    f"{brand_name} customer support and features"
                ],
                recommended_title=f"{brand_name} | Official {category} Platform",
                meta_description=description[:155],
                supporting_content=[
                    f"Dedicated '{category} Solutions' overview landing page",
                    f"Comprehensive '{brand_name} Getting Started' FAQ hub",
                    "Customer case studies showcasing measurable outcomes",
                    "Comparison articles highlighting unique product advantages"
                ],
                research_disclaimer="Live search volumes, keyword difficulty scores, and current ranking positions require access to third-party search engine API data and specialized SEO tools. The recommendations provided are strategic suggestions based on keyword relevance and competitive analysis."
            ),
            top_services=services[:5],
            target_audience=TargetAudience(
                primary_audience=[
                    AudienceProfile(
                        audience="Direct Digital Consumers & Practitioners",
                        business_type="B2C / B2B",
                        requirement=f"Access to efficient, reliable {category.lower()} tools and services.",
                        customer_needs=["Fast workflow completion", "Clear pricing", "Intuitive navigation"],
                        interests=["Productivity tools", "Modern digital solutions", "Value for money"]
                    )
                ],
                secondary_audience=[
                    AudienceProfile(
                        audience="Teams & Small Business Owners",
                        business_type="B2B",
                        requirement="Scalable platforms that streamline operations and improve output quality.",
                        customer_needs=["Collaboration", "Reliable support", "Cost effectiveness"],
                        interests=["Operational efficiency", "Business scaling", "Software integration"]
                    )
                ],
                industries=[category, "Technology", "Consumer Services"],
                geographical_focus=["Global (Digital Access)"],
                customer_needs=[
                    "High reliability and continuous service availability",
                    "Competitive value proposition and clear product utility",
                    "Intuitive user interface with minimal learning curve"
                ],
                recommended_segments=[
                    "Active digital practitioners seeking productivity gains",
                    "Small-to-medium business operators evaluating modern software",
                    "Early adopters and tech-focused consumers"
                ]
            )
        )
    )
