
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# Base model
class SchemaBase(BaseModel):
    pass


# -------------------------------
# REQUEST MODEL
# -------------------------------

class LinkRequest(SchemaBase):
    model_config = ConfigDict(extra="forbid")
    url: HttpUrl


# -------------------------------
# BRAND MODEL
# -------------------------------

class Brand(SchemaBase):
    name: str
    category: str
    summary: str


# -------------------------------
# COMPETITOR ANALYSIS
# -------------------------------

class Competitor(SchemaBase):
    name: str
    website: str | None = None
    overview: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses_or_gaps: list[str] = Field(default_factory=list)

    source_type: Literal[
        "external_research",
        "model_knowledge",
        "inferred"
    ]


class CompetitorAnalysis(SchemaBase):
    brand_overview: str

    competitors: list[Competitor] = Field(
        default_factory=list
    )

    strengths: list[str] = Field(default_factory=list)

    opportunities: list[str] = Field(default_factory=list)

    methodology_note: str = Field(
        default="Competitor comparisons are model-generated observational assessments; specific performance metrics require direct empirical verification."
    )


# -------------------------------
# SEARCH QUERY ANALYSIS
# -------------------------------

Platform = Literal[
    "Google",
    "Facebook",
    "Instagram",
    "LinkedIn",
    "X",
    "Twitter"
]


class TargetSearchQuery(SchemaBase):
    query: str

    platforms: list[Platform] = Field(
        default_factory=list
    )

    intent: str

    business_relevance: str

    target_audience: str


# -------------------------------
# SEO IMPROVEMENTS
# -------------------------------

class SEOImprovements(SchemaBase):
    primary_keyword: str

    secondary_keywords: list[str] = Field(
        default_factory=list
    )

    long_tail_keywords: list[str] = Field(
        default_factory=list
    )

    recommended_title: str

    meta_description: str

    supporting_content: list[str] = Field(
        default_factory=list
    )

    research_disclaimer: str = Field(
        default="Keyword and content suggestions are AI-generated strategic recommendations. Measured search volume, keyword difficulty, and live ranking data require dedicated SEO provider API integration."
    )


# -------------------------------
# SERVICES / CAPABILITIES
# -------------------------------

class Service(SchemaBase):
    name: str

    description: str

    target_industry: str

    target_customer: str

    main_benefit: str

    identification_type: Literal[
        "website_evidence",
        "inferred_recommendation"
    ]

    evidence: str | None = Field(
        default=None,
        description="Exact quote, button text, or metadata excerpt from the extracted website content supporting this offering."
    )


# -------------------------------
# TARGET AUDIENCE
# -------------------------------

class AudienceProfile(SchemaBase):
    audience: str

    business_type: str

    requirement: str

    customer_needs: list[str] = Field(
        default_factory=list
    )

    interests: list[str] = Field(
        default_factory=list
    )


class TargetAudience(SchemaBase):
    primary_audience: list[AudienceProfile] = Field(
        default_factory=list
    )

    secondary_audience: list[AudienceProfile] = Field(
        default_factory=list
    )

    industries: list[str] = Field(
        default_factory=list
    )

    geographical_focus: list[str] = Field(
        default_factory=list
    )

    customer_needs: list[str] = Field(
        default_factory=list
    )

    recommended_segments: list[str] = Field(
        default_factory=list
    )


# -------------------------------
# COMPLETE ANALYSIS
# -------------------------------

class Analysis(SchemaBase):
    competitor_analysis: CompetitorAnalysis

    target_search_queries: list[TargetSearchQuery] = Field(
        default_factory=list
    )

    seo_improvements: SEOImprovements

    top_services: list[Service] = Field(
        default_factory=list
    )

    target_audience: TargetAudience


# -------------------------------
# FINAL API RESPONSE
# -------------------------------

class LinkAnalysisResponse(SchemaBase):
    success: bool = True

    website: str

    brand: Brand

    analysis: Analysis
