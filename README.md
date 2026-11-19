# AI-Powered Website Link Analysis API

A security-conscious, production-oriented FastAPI application that analyzes supported public HTTP/HTTPS websites, extracts rich semantic content (HTML, metadata, Open Graph, Schema.org JSON-LD, navigation hierarchy, interactive actions), and uses a **provider-independent intelligence architecture** (Google Gemini Free Cloud, Local Ollama, and a Deterministic Offline Rule Engine) to generate structured business intelligence across 5 key areas: **Competitor Analysis**, **Target Search Queries**, **SEO Recommendations**, **Top 5 Services/Capabilities**, and **Target Audience Profiling**.

---

## 1. Project Overview

The application accepts a target website URL, safely fetches its content, extracts core business signals, and evaluates the website using an LLM or offline heuristics to return a strictly typed, evidence-grounded JSON report.

### High-Availability Cascade Flow
```text
User Request (POST /link-analysis)
               │
               ▼
   [ URL Validation & SSRF Guard ]  ──► Rejects private IPs, localhost, non-standard ports
               │
               ▼
   [ Anti-TOCTOU Network Connection ] ──► Resolves & pins socket directly to validated global IP
               │
               ▼
   [ Website Content Extractor ]    ──► Streams HTML (max 2MB), extracts title, meta,
               │                        Open Graph, Schema.org JSON-LD, navigation & headings
               │
               ▼
   [ In-Memory URL Cache ]          ──► Checks TTL & functional query key (0 tokens if hit)
               │
               ▼
   [ Provider Dispatcher ]
   ┌─────────────────────────────────────────────────────────────┐
   │ 1. Primary: Google Gemini 2.5 Flash (Cloud API)             │
   │ 2. Fallback: Ollama Local Models (e.g., qwen2.5:3b)         │
   │ 3. Fail-Safe: Deterministic Offline Rule-Based Engine       │
   └─────────────────────────────────────────────────────────────┘
               │
               ▼
   [ Pydantic Schema Validation ]   ──► Validates structure, evidence citations & disclaimers
               │
               ▼
   Structured JSON Response         ──► 5 Comprehensive Sections
```

---

## 2. Architecture and Project Structure

```text
ai-link-analysis/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, endpoints, middleware, exception handlers
│   ├── config.py                   # Multi-provider configuration (Gemini, Ollama, Cache, Port)
│   ├── schemas.py                  # Pydantic v2 data models with evidence citation fields
│   ├── services/
│   │   ├── __init__.py
│   │   ├── website_extractor.py    # Safe HTTP streaming, HTML parsing, metadata & JSON-LD
│   │   ├── competitor_service.py   # Competitor clues & domain relationship analysis
│   │   ├── llm_service.py          # Google Gemini integration with strict evidence prompt
│   │   ├── ollama_service.py       # Zero-cost local LLM integration (Ollama / qwen2.5:3b)
│   │   ├── offline_analyzer.py     # Deterministic offline rule-based fallback (no external API)
│   │   ├── cache_service.py        # URL-normalized in-memory cache with TTL and LRU eviction
│   │   ├── llm_provider.py         # Unified multi-provider dispatcher & cascade router
│   │   └── analysis_service.py     # Pipeline coordinator & HTTP error mapper
│   └── utils/
│       ├── __init__.py
│       └── validators.py           # Strict URL validation, SSRF defense & connect-time IP pinning
├── tests/
│   ├── __init__.py
│   └── test_link_analysis.py       # 16 Unit, security, and integration tests
├── Dockerfile                      # Production container image definition
├── docker-compose.yml              # Container orchestration configuration
├── .dockerignore                   # Docker build context exclusions
├── sample_analysis.json            # Real live analysis output
├── test_extractor.py               # Standalone test for web scraping pipeline
├── test_llm.py                     # Standalone test for end-to-end LLM generation
├── test_schemas.py                 # Standalone test for Pydantic schema validation
├── .env.example                    # Template for environment variables
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation & research report
```

---

## 3. Features

- **Provider-Independent Intelligence**: Seamlessly runs with Google Gemini, local Ollama, or a built-in deterministic rule engine when no external API is available.
- **Strict Evidence Grounding**: Core services marked `website_evidence` must quote exact text, button labels, or metadata from the extracted website content.
- **SSRF & Anti-DNS-Rebinding Defense**: Validates URL structure, restricts ports to 80/443, enforces `ip.is_global` against IPv4 and IPv6, and binds the socket to the validated IP at connect time.
- **High-Fidelity Caching**: In-memory cache strips marketing tracking query parameters (`utm_*`, `fbclid`), strictly preserves functional parameters (`?id=1` vs `?id=2`), enforces TTL expiration, and returns isolated copies with the requested URL preserved.
- **Responsible Market Intelligence**: Competitor comparisons derived from model knowledge include clear methodology notes; SEO suggestions include explicit disclaimers indicating they are strategic suggestions rather than measured search engine ranking metrics.

---

## 4. Installation and Quickstart

### Prerequisites
- Python 3.10+ (tested on Python 3.11 and 3.14)
- Git

### Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/variantbyx/ai-link-analyzer
   cd ai-link-analysis
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Select your desired operational mode in `.env`:

   - **Mode A: Cloud Free Tier (Recommended)**
     ```env
     LLM_PROVIDER=auto
     GEMINI_API_KEY=your_gemini_api_key
     GEMINI_MODEL=gemini-2.5-flash
     ENABLE_CACHE=true
     ```
     *Attempts Gemini first. If quota limit (429) or outage occurs, cascades to local Ollama (if running) or the Deterministic Offline Engine.*

   - **Mode B: Offline Mode (No External API Required)**
     ```env
     LLM_PROVIDER=offline
     ENABLE_CACHE=true
     ```
     *Runs locally using deterministic rule-based heuristics without external network API calls.*

   - **Mode C: Local Open-Weight AI (Ollama)**
     ```env
     LLM_PROVIDER=ollama
     OLLAMA_BASE_URL=http://localhost:11434
     OLLAMA_MODEL=qwen2.5:3b
     ENABLE_CACHE=true
     ```
     *Requires Ollama installed and running locally with the target model pulled (`ollama pull qwen2.5:3b`).*

5. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 4000 --reload
   ```

6. **Access Interactive API Docs**:
   - Swagger UI: [http://127.0.0.1:4000/docs](http://127.0.0.1:4000/docs)
   - ReDoc: [http://127.0.0.1:4000/redoc](http://127.0.0.1:4000/redoc)

---

## 5. Environment Variables

| Variable | Description | Default Value | Required? |
|---|---|---|---|
| `LLM_PROVIDER` | Selection mode: `auto`, `gemini`, `ollama`, or `offline` | `auto` | No |
| `GEMINI_API_KEY` | Google Gemini API key from Google AI Studio | `""` | Yes (for Gemini/Auto) |
| `GEMINI_MODEL` | Gemini model variant | `gemini-2.5-flash` | No |
| `OLLAMA_BASE_URL` | Local Ollama server address | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Local Ollama model identifier | `qwen2.5:3b` | No |
| `ENABLE_CACHE` | Enable or disable in-memory URL analysis caching | `true` | No |
| `CACHE_TTL_SECONDS` | In-memory cache expiration lifespan in seconds | `3600` (1 hour) | No |
| `CACHE_MAX_SIZE` | Maximum cached URLs before LRU eviction | `500` | No |
| `API_HOST` | FastAPI server bind address | `0.0.0.0` | No |
| `API_PORT` | FastAPI server listening port | `4000` | No |

---

## 6. API Specification and Examples

### Endpoint
`POST /link-analysis`

### Request Body
```json
{
  "url": "https://www.walmart.com"
}
```

### Response Example (Abbreviated)
> *Note: The following response is abbreviated for documentation purposes. The actual API returns five target search queries and five services.*

```json
{
  "success": true,
  "website": "https://www.walmart.com",
  "brand": {
    "name": "Walmart",
    "category": "Retail & Supermarkets",
    "summary": "Walmart Inc. is an American multinational retail corporation operating a chain of hypermarkets, discount department stores, and grocery stores."
  },
  "analysis": {
    "competitor_analysis": {
      "brand_overview": "Walmart provides low-cost grocery, apparel, household, and electronic goods online and via physical retail locations.",
      "competitors": [
        {
          "name": "Amazon",
          "website": "https://www.amazon.com",
          "overview": "Global e-commerce and cloud infrastructure leader.",
          "strengths": ["Massive e-commerce selection", "Fast Prime delivery", "Marketplace scale"],
          "weaknesses_or_gaps": ["Fewer physical retail locations for grocery pickup"],
          "source_type": "model_knowledge"
        },
        {
          "name": "Target",
          "website": "https://www.target.com",
          "overview": "General merchandise retailer focused on trendy, affordable design and omni-channel shopping.",
          "strengths": ["Strong private-label brands", "Design appeal", "Curbside Drive Up"],
          "weaknesses_or_gaps": ["Smaller grocery market share compared to Walmart"],
          "source_type": "model_knowledge"
        },
        {
          "name": "Kroger",
          "website": "https://www.kroger.com",
          "overview": "Major US grocery supermarket chain operating physical supermarkets and digital fulfillment.",
          "strengths": ["Extensive supermarket footprint", "Loyalty discounts", "Fresh food assortment"],
          "weaknesses_or_gaps": ["Less diversified general merchandise compared to supercenters"],
          "source_type": "model_knowledge"
        }
      ],
      "strengths": ["Every Day Low Prices", "Broad product assortment", "Walmart+ delivery"],
      "opportunities": ["Enhanced personalization", "Same-day delivery expansion"],
      "methodology_note": "Competitor comparisons reflect model-generated market observations and general industry knowledge. Specific market share, financial performance, or detailed feature parity would require empirical, real-time data from market research firms."
    },
    "target_search_queries": [
      {
        "query": "Walmart online grocery delivery near me",
        "platforms": ["Google", "Facebook"],
        "intent": "Commercial / Transactional",
        "business_relevance": "Direct intent to purchase household groceries for home delivery.",
        "target_audience": "Busy parents, families, suburban households"
      }
    ],
    "seo_improvements": {
      "primary_keyword": "online grocery delivery",
      "secondary_keywords": ["curbside pickup", "discount household goods", "affordable electronics"],
      "long_tail_keywords": ["same day grocery delivery near me affordable", "order groceries online with store pickup"],
      "recommended_title": "Walmart | Save Money. Live Better. Online Grocery & Shopping",
      "meta_description": "Shop Walmart.com for Everyday Low Prices. Free shipping on orders $35+ or pickup in store.",
      "supporting_content": ["Weekly savings circular page", "Grocery delivery subscription guide"],
      "research_disclaimer": "Live search volumes, keyword difficulty scores, and current ranking positions require access to third-party search engine API data and specialized SEO tools. The recommendations provided are strategic suggestions based on keyword relevance and competitive analysis."
    },
    "top_services": [
      {
        "name": "Walmart+ Membership",
        "description": "Subscription offering unlimited free store delivery and no minimum shipping.",
        "target_industry": "Consumer Retail & E-commerce",
        "target_customer": "Frequent shoppers and families",
        "main_benefit": "Save time and delivery fees on everyday orders",
        "identification_type": "website_evidence",
        "evidence": "Walmart+ membership benefits including free delivery"
      }
    ],
    "target_audience": {
      "primary_audience": [
        {
          "audience": "Value-Conscious Families",
          "business_type": "B2C",
          "requirement": "Affordable household essentials and groceries",
          "customer_needs": ["Low prices", "Convenient delivery"],
          "interests": ["Budgeting", "Saving money"]
        }
      ],
      "secondary_audience": [],
      "industries": ["Retail", "Grocery", "Consumer Goods"],
      "geographical_focus": ["United States"],
      "customer_needs": ["Affordability", "Reliability", "Wide selection"],
      "recommended_segments": ["Budget-Conscious Families", "Online Grocery Shoppers"]
    }
  }
}
```

---

## 7. Security and Robustness

### SSRF & Anti-DNS-Rebinding Defense
1. **Upfront URL Validation**:
   - Enforces HTTP/HTTPS schemes only and rejects embedded credentials (`user:pass@host`).
   - Restricts ports strictly to standard web ports (80 and 443).
   - Rejects `localhost` and `*.localhost`.
   - Asynchronously resolves hostnames via `asyncio.get_running_loop().getaddrinfo()`.
   - Enforces `ipaddress.ip_address(ip).is_global` against all resolved IP addresses, blocking IPv4 private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), IPv4/IPv6 loopback (`127.0.0.1`, `::1`), link-local metadata endpoints (`169.254.169.254`, `fe80::/10`), unique local IPv6 (`fc00::/7`), and reserved address spaces.

2. **Socket-Level IP Pinning (Anti-TOCTOU)**:
   - Mitigates Time-of-Check to Time-of-Use (TOCTOU) DNS rebinding attacks via a custom `SSRFSafeNetworkBackend` in HTTPX.
   - When HTTPX opens a TCP connection, the backend re-resolves the target host at the moment of connection establishment, re-verifies global routability, and binds the socket directly to the validated IP address.
   - Preserves the target hostname for TLS SNI and HTTP `Host` header validation.

3. **Manual Redirect Following**:
   - Disables automatic HTTP client redirect following.
   - Manually follows redirects (up to 5 hops maximum) and re-evaluates each redirect target URL and its resolved IP address through the SSRF validation and socket-pinning pipeline.

### Scraper Safeguards & Content Parsing
1. **Streaming Size Cap**: Streams byte chunks and aborts immediately if the response body exceeds 2 MB (`MAX_HTML_SIZE`).
2. **De-noising & Filtering**: Filters in-page tracking fragments (`#...`), non-navigational protocols (`mailto:`, `tel:`, `javascript:`), and de-duplicates navigation links.
3. **Structured Data Extraction**: Automatically harvests Schema.org JSON-LD scripts (`<script type="application/ld+json">`) to extract structured corporate identities and organization metadata.
4. **SPA and JavaScript-Rendered Website Limitations**:
   The extractor uses HTTPX to retrieve server-delivered HTML and BeautifulSoup to parse its DOM. It does not execute JavaScript or perform browser-based hydration. For websites that return meaningful server-rendered HTML, it extracts available content, metadata, headings, links, and interactive labels. For JavaScript-heavy websites that return an empty application shell, the extracted information may be incomplete. Browser automation is intentionally excluded to keep the application lightweight.

### Cache Integrity & Expiry
1. **Collision-Free Key Normalization**: Normalizes schemes and domains to lowercase, removes standard web ports, strips marketing/tracking query parameters (`utm_*`, `fbclid`, `gclid`, `ref`), but strictly preserves and sorts functional query parameters (`?id=1` vs `?id=2`), preventing cross-URL collisions.
2. **Time-to-Live (TTL) Expiry**: Each cached entry records its timestamp and automatically expires after `CACHE_TTL_SECONDS` (default: 3600 seconds / 1 hour).
3. **Failure Isolation**: Analyses that produce errors or return `success: false` are rejected by the cache, ensuring only valid analyses are stored.
4. **Deep Copy Isolation**: Returns deep copies of cached models with the caller's requested URL preserved, preventing mutations to internal cache state.
5. **LRU Capacity Cap**: Built on `collections.OrderedDict` with an LRU cap (`CACHE_MAX_SIZE=500`) to prevent unbounded memory growth.

---

## 8. LLM Platform & Model Research (Cost, Speed & Accuracy)

### A. Published LLM Pricing Rate Cards (Checked November 2026)

| Model | Provider | Input Pricing (per 1M tokens) | Output Pricing (per 1M tokens) | Context Window | Native Structured JSON |
|---|---|---|---|---|---|
| **Google Gemini 2.5 Flash** (Selected) | Google DeepMind | **$0.30** (standard paid) / **$0.00** (free tier) | **$2.50** (standard paid) / **$0.00** (free tier) | 1,000,000 tokens | Direct Pydantic `response_schema` |
| **OpenAI GPT-4o-mini** | OpenAI | **$0.15** | **$0.60** | 128,000 tokens | `response_format: json_schema` |
| **Anthropic Claude 3.5 Sonnet** | Anthropic | **$3.00** | **$15.00** | 200,000 tokens | Tool Use / JSON output |
| **Ollama (Qwen 2.5 3B)** | Open-Source / Local | **$0.00** (local compute) | **$0.00** (local compute) | 32,768 tokens | JSON mode (`format="json"`) |

*Pricing sources: Official published rate cards from [Google Gemini API Pricing](https://ai.google.dev/pricing), OpenAI Pricing, and Anthropic Pricing docs as of November 2026.*

### B. Cost Economics (Per 1,000 Analysis Requests)

Assuming a typical analysis payload of **2,500 input tokens** (extracted HTML, metadata, and JSON-LD) and **1,200 output tokens** (5-section business JSON report):

$$\text{Cost per Request} = \frac{(\text{Input Tokens} \times \text{Input Rate}) + (\text{Output Tokens} \times \text{Output Rate})}{1,000,000}$$

- **Google Gemini 2.5 Flash (Free Tier)**:
  $$\text{Cost} = \$0.00 \quad (\text{Free up to rate limits: 15 RPM / project quotas})$$
- **Google Gemini 2.5 Flash (Standard Paid Tier)**:
  $$\text{Cost} = \frac{(2,500 \times \$0.30) + (1,200 \times \$2.50)}{1,000,000} = \$0.00075 + \$0.00300 = \$0.00375 \text{ per request}$$
  $$\text{Cost for 1,000 Requests} \approx \mathbf{\$3.75}$$
- **OpenAI GPT-4o-mini**:
  $$\text{Cost} = \frac{(2,500 \times \$0.15) + (1,200 \times \$0.60)}{1,000,000} = \$0.000375 + \$0.000720 = \$0.001095 \text{ per request}$$
  $$\text{Cost for 1,000 Requests} \approx \mathbf{\$1.10}$$
- **Anthropic Claude 3.5 Sonnet**:
  $$\text{Cost} = \frac{(2,500 \times \$3.00) + (1,200 \times \$15.00)}{1,000,000} = \$0.0075 + \$0.0180 = \$0.0255 \text{ per request}$$
  $$\text{Cost for 1,000 Requests} \approx \mathbf{\$25.50}$$

### C. Model Selection Justification

1. **Free Developer Tier**: Google Gemini offers a free tier supporting up to 15 requests per minute, making it optimal for zero-budget development and evaluation.
2. **Context Window (1M Tokens)**: E-commerce and enterprise homepages have large DOM structures. Gemini's 1M context window ensures extensive page content never triggers input context overflow.
3. **Native Pydantic Schema Enforcement**: Gemini directly accepts Pydantic models through `response_schema`, validating JSON structures at the token-generation level.
4. **Cost Tradeoff Analysis**: While OpenAI's GPT-4o-mini is more economical on standard paid tiers for output tokens ($0.60 vs $2.50 per 1M), Gemini 2.5 Flash provides a free tier, larger context, and competitive prompt caching for enterprise deployments.
5. **Qualitative Assessment**: No independent, quantitative accuracy benchmark was conducted for this assignment. Qualitative evaluation across test URLs demonstrates that Gemini 2.5 Flash accurately follows complex Pydantic JSON schemas and reliably isolates on-page text evidence for service citations.
6. **Measured Local Latency**: In our local integration test suite (`test_llm.py`), Gemini 2.5 Flash achieved an end-to-end turnaround of **4.5 to 7.5 seconds** for scraping, prompt assembly, and 5-section JSON generation.

---

## 9. Cost Optimization Techniques Implemented

- **HTML Pre-cleaning**: Removes `<script>`, `<style>`, `<svg>`, `<iframe>`, and redundant whitespace, reducing payload size by over **85%** before passing to the model.
- **Priority Signal Extraction**: Extracts structured Schema.org JSON-LD and meta tags first, giving the model concise facts without bloating the prompt.
- **Navigation Capping**: Limits extracted internal links to the top 20 relevant items.
- **In-Memory URL Caching**: Avoids redundant LLM invocations for previously analyzed URLs.
- **Single-Pass Inference**: Generates all 5 analysis sections in a single structured prompt call, eliminating multi-round latency and redundant input token costs.

---

## 10. Testing and Test Coverage

The project includes **16 unit, security, and integration tests** built with Python's standard `unittest` framework and FastAPI's `TestClient`.

### Run Test Suite
```bash
python -m unittest -v tests.test_link_analysis
```

### Verified Test Suite
1. `test_health_endpoint`: Validates `/health` check.
2. `test_home_endpoint`: Validates `/` metadata and discovery.
3. `test_link_analysis_invalid_url_format`: Verifies rejection of malformed URLs (HTTP 422).
4. `test_link_analysis_localhost_blocked`: Verifies SSRF rejection of localhost URLs (HTTP 400/403).
5. `test_validate_url_rejects_localhost`: Unit test for loopback host rejection.
6. `test_validate_url_rejects_ftp`: Unit test enforcing HTTP/HTTPS schemes only.
7. `test_validate_url_rejects_non_standard_port`: Unit test restricting ports to 80 and 443.
8. `test_dns_rebinding_backend_blocks_private_ip`: Direct socket-layer test verifying `SSRFSafeNetworkBackend` rejects loopback, RFC 1918 private IPs, and non-standard ports.
9. `test_cache_service_normalization_and_storage`: Validates URL key normalization and cache round-trip.
10. `test_cache_different_urls_do_not_share_results`: Ensures distinct functional query strings (`?id=1` vs `?id=2`) never collide or share cache entries.
11. `test_cache_expiry_ttl`: Validates TTL expiration and automatic eviction.
12. `test_failed_analysis_not_cached`: Guarantees unverified or failed analyses are never stored in cache.
13. `test_cached_response_retains_requested_url`: Verifies that cached responses return deep copies with the caller's requested URL preserved.
14. `test_extract_content_html_parsing`: Verifies parsing of HTML, meta tags, and Schema.org JSON-LD.
15. `test_offline_analyzer_generation`: Verifies deterministic 5-section offline generation.
16. `test_link_analysis_mocked_success`: Complete end-to-end endpoint test with mocked services.

---

## 11. Docker and Deployment

### Docker Compose (Recommended)
```bash
docker compose up --build
```

### Standalone Docker CLI
```bash
docker build -t ai-link-analysis .
docker run -p 4000:4000 --env-file .env ai-link-analysis
```

### Cloud Deployment (Render / Railway / Fly.io / VPS)
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 4000`
- **Environment Variables**: Configure `GEMINI_API_KEY`, `LLM_PROVIDER=auto`, and `API_PORT=4000`.

---

## 12. Error Handling and Known Limitations

### Error Handling Specification

| Scenario | HTTP Status | Response Structure | Behavior |
|---|---|---|---|
| **Malformed URL** | `422 Unprocessable` | `{"success": false, "error": "Validation Error...", "details": [...]}` | Rejected by Pydantic `HttpUrl` validation. |
| **Localhost / Private IP** | `400 Bad Request` | `{"success": false, "error": "Only ports 80 and 443...", "status_code": 400}` | Blocked by SSRF validator / network backend. |
| **DNS Resolution Failure** | `400 Bad Request` | `{"success": false, "error": "Unable to resolve website hostname.", ...}` | Triggered when domain does not exist. |
| **Target Website Down / 5xx** | `502 Bad Gateway` | `{"success": false, "error": "Failed to extract website content...", ...}` | Triggered on HTTP 4xx/5xx responses from target. |
| **Request Timeout** | `504 Gateway Timeout` | `{"success": false, "error": "Website request timed out...", ...}` | Triggered if target website takes > 20s to respond. |
| **Daily LLM Quota Exhausted** | `200 OK` (Cascaded) or `429 Too Many Requests` | Returns offline analysis in `auto` mode; returns 429 if provider is strictly `gemini`. | Distinguishes daily quota exhaustion from transient rate spikes; cascades immediately to offline fallback in `auto` mode. |

### Disclaimers & Known Limitations
- **JavaScript-Rendered Websites**: Content is fetched via HTTP streaming and parsed via BeautifulSoup. Websites requiring client-side JavaScript execution (SPAs) will only yield server-rendered markup, metadata, and fallback DOM text.
- **In-Memory Cache Lifecycle**: The default cache resides in memory and resets when the process restarts. For multi-instance production environments, an external cache such as Redis should be configured.
- **Competitor Intelligence Scope**: Competitor comparisons derived from model knowledge represent general market observations. They do not constitute real-time financial or market-share research.
- **SEO Metric Scope**: SEO keyword suggestions and content roadmaps are strategic recommendations based on semantic analysis. They do not represent live keyword search volume, keyword difficulty, or active search engine rank positions.

---

## 13. Future Improvements

- **Browser-Based Scraping Worker**: Optional integration of Playwright for client-side rendered Single-Page Applications.
- **Distributed Cache & Rate Limiting**: Integration of Redis for shared multi-worker caching and sliding-window rate limiting.
- **SEO Data Provider Integration**: Webhook or API integration with third-party SEO indexing providers (e.g., DataForSEO, Ahrefs API) for live search volumes.
