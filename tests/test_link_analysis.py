import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import LinkAnalysisResponse
from app.utils.validators import validate_url
from app.services.website_extractor import extract_content
from app.services.offline_analyzer import generate_offline_analysis
from app.services.cache_service import get_cached_analysis, set_cached_analysis, clear_cache, normalize_cache_url


client = TestClient(app)


class TestLinkAnalysisAPI(unittest.TestCase):

    def setUp(self):
        clear_cache()

    def test_home_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("provider", data)
        self.assertIn("model", data)

    def test_health_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("provider", data)

    def test_link_analysis_invalid_url_format(self):
        response = client.post("/link-analysis", json={"url": "not-a-valid-url"})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertFalse(data["success"])

    def test_link_analysis_localhost_blocked(self):
        response = client.post("/link-analysis", json={"url": "http://localhost:8000"})
        self.assertIn(response.status_code, (400, 403))
        data = response.json()
        self.assertFalse(data["success"])

    def test_validate_url_rejects_localhost(self):
        async def run():
            with self.assertRaises(ValueError):
                await validate_url("http://localhost:8080")
        asyncio.run(run())

    def test_validate_url_rejects_ftp(self):
        async def run():
            with self.assertRaises(ValueError):
                await validate_url("ftp://example.com")
        asyncio.run(run())

    def test_validate_url_rejects_non_standard_port(self):
        async def run():
            with self.assertRaises(ValueError):
                await validate_url("http://example.com:8080")
        asyncio.run(run())

    def test_extract_content_html_parsing(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
          <head>
            <title>TechFlow - AI Cloud Solutions</title>
            <meta name="description" content="Next-generation cloud infrastructure for fast-growing businesses.">
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@type": "Organization",
              "name": "TechFlow Inc",
              "description": "Enterprise cloud and AI platform"
            }
            </script>
          </head>
          <body>
            <nav>
              <a href="/services">Services</a>
              <a href="/pricing">Pricing</a>
              <a href="/about">About Us</a>
            </nav>
            <main>
              <h1>Transform Your Cloud Infrastructure</h1>
              <h2>High Performance Serverless Clusters</h2>
              <p>We provide enterprise-grade Kubernetes management, automated failover, and custom AI model serving.</p>
            </main>
          </body>
        </html>
        """
        data = extract_content(sample_html, "https://techflow.io")

        self.assertEqual(data["title"], "TechFlow - AI Cloud Solutions")
        self.assertIn("Next-generation cloud infrastructure", data["description"])
        self.assertIn("Transform Your Cloud Infrastructure", data["headings"])
        self.assertGreater(len(data["json_ld"]), 0)
        self.assertEqual(data["json_ld"][0]["name"], "TechFlow Inc")
        self.assertGreaterEqual(len(data["links"]), 3)

    def test_offline_analyzer_generation(self):
        dummy_data = {
            "url": "https://samplemarket.com",
            "title": "SampleMarket | Online Shopping and Groceries",
            "description": "Buy fresh groceries, electronics, and fashion online.",
            "headings": ["Fresh Groceries", "Home & Living", "Electronics Deals"],
            "button_actions": ["Add to Cart", "Shop Now"],
            "json_ld": []
        }
        res = generate_offline_analysis(dummy_data)
        self.assertTrue(res.success)
        self.assertEqual(res.brand.name, "SampleMarket")
        self.assertEqual(len(res.analysis.competitor_analysis.competitors), 3)
        self.assertEqual(len(res.analysis.top_services), 5)
        self.assertEqual(len(res.analysis.target_search_queries), 5)
        self.assertIn("methodology_note", res.analysis.competitor_analysis.__class__.model_fields)

    def test_cache_service_normalization_and_storage(self):
        url = "https://example.com/products/?utm_source=test"
        normalized = normalize_cache_url(url)
        self.assertEqual(normalized, "https://example.com/products")

        dummy_data = {
            "url": "https://cached-example.com",
            "title": "Cached Example",
            "description": "A cached test page",
            "headings": ["Feature 1", "Feature 2"],
            "button_actions": ["Get Started"],
            "json_ld": []
        }
        res = generate_offline_analysis(dummy_data)
        set_cached_analysis("https://cached-example.com/", res)

        cached_hit = get_cached_analysis("https://cached-example.com")
        self.assertIsNotNone(cached_hit)
        self.assertEqual(cached_hit.brand.name, res.brand.name)

    @patch("app.services.analysis_service.extract_website", new_callable=AsyncMock)
    @patch("app.services.analysis_service.generate_analysis_unified", new_callable=AsyncMock)
    def test_link_analysis_mocked_success(self, mock_unified, mock_extract):
        mock_extract.return_value = {
            "url": "https://sampletech.com",
            "title": "SampleTech Solutions",
            "description": "IT and Cloud consulting services.",
            "meta_keywords": "cloud, it",
            "og_data": {},
            "json_ld": [],
            "headings": ["Cloud Solutions", "Managed Services"],
            "content": "SampleTech provides premier cloud and cybersecurity services for enterprises.",
            "links": [{"text": "Solutions", "url": "https://sampletech.com/solutions"}]
        }

        mock_unified.return_value = (LinkAnalysisResponse.model_validate({
            "success": True,
            "website": "https://sampletech.com",
            "brand": {
                "name": "SampleTech",
                "category": "Information Technology",
                "summary": "Enterprise cloud and cybersecurity consulting firm."
            },
            "analysis": {
                "competitor_analysis": {
                    "brand_overview": "SampleTech is a regional IT consulting leader.",
                    "competitors": [
                        {
                            "name": "Accenture",
                            "website": "https://accenture.com",
                            "overview": "Global IT consulting powerhouse.",
                            "strengths": ["Global scale"],
                            "weaknesses_or_gaps": ["High cost"],
                            "source_type": "model_knowledge"
                        }
                    ],
                    "strengths": ["Agile teams"],
                    "opportunities": ["AI adoption"]
                },
                "target_search_queries": [
                    {
                        "query": "enterprise cloud migration services",
                        "platforms": ["Google", "LinkedIn"],
                        "intent": "Service Search",
                        "business_relevance": "Direct match for core consulting offerings.",
                        "target_audience": "CTOs and IT Directors"
                    }
                ],
                "seo_improvements": {
                    "primary_keyword": "enterprise cloud migration",
                    "secondary_keywords": ["managed IT", "cybersecurity"],
                    "long_tail_keywords": ["best cloud migration partner for enterprise"],
                    "recommended_title": "SampleTech | Enterprise Cloud & Cybersecurity Solutions",
                    "meta_description": "Modernize your infrastructure with SampleTech's managed cloud consulting.",
                    "supporting_content": ["Cloud migration roadmap guide"]
                },
                "top_services": [
                    {
                        "name": "Cloud Infrastructure Migration",
                        "description": "Full-lifecycle AWS and Azure migration.",
                        "target_industry": "Financial Services, Healthcare",
                        "target_customer": "Mid-to-large enterprises",
                        "main_benefit": "Zero downtime cloud adoption",
                        "identification_type": "website_evidence",
                        "evidence": "SampleTech provides premier cloud and cybersecurity services for enterprises."
                    }
                ],
                "target_audience": {
                    "primary_audience": [
                        {
                            "audience": "Enterprise IT Decision Makers",
                            "business_type": "B2B",
                            "requirement": "Scalable cloud architecture",
                            "customer_needs": ["Security", "Compliance"],
                            "interests": ["DevOps", "FinOps"]
                        }
                    ],
                    "secondary_audience": [],
                    "industries": ["Information Technology"],
                    "geographical_focus": ["North America"],
                    "customer_needs": ["Cost control"],
                    "recommended_segments": ["Mid-market B2B enterprises"]
                }
            }
        }), "mocked_provider")

        response = client.post("/link-analysis", json={"url": "https://sampletech.com"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["brand"]["name"], "SampleTech")
        self.assertEqual(len(data["analysis"]["target_search_queries"]), 1)
        self.assertEqual(data["analysis"]["top_services"][0]["name"], "Cloud Infrastructure Migration")


if __name__ == "__main__":
    unittest.main()
