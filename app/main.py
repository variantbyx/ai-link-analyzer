from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas import LinkRequest, LinkAnalysisResponse
from app.services.analysis_service import process_link_analysis, AnalysisServiceError
from app.config import GEMINI_MODEL, LLM_PROVIDER


app = FastAPI(
    title="AI-Powered Website Link Analysis API",
    description=(
        "Comprehensive website analysis API with multi-provider architecture: "
        "Gemini (Free Cloud), Ollama (Local Zero-Cost), and Deterministic Offline Engine. "
        "Generates Competitor intelligence, Target Search Queries across 5 platforms, "
        "SEO Improvements, Top 5 Services/Capabilities, and Target Audience Profiles."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AnalysisServiceError)
async def analysis_service_exception_handler(request: Request, exc: AnalysisServiceError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msg = errors[0].get("msg") if errors else "Invalid request payload."
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": f"Validation Error: {error_msg}",
            "details": errors
        }
    )


@app.get("/", tags=["Health"])
def home():
    """Service status and meta info."""
    return {
        "status": "online",
        "service": "AI-Powered Website Link Analysis API",
        "provider": LLM_PROVIDER,
        "model": GEMINI_MODEL,
        "docs": "/docs",
        "endpoint": "POST /link-analysis"
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "provider": LLM_PROVIDER,
        "model": GEMINI_MODEL
    }


@app.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Analyze website URL",
    description=(
        "Fetches the website, extracts metadata and content safely, "
        "and runs an AI analysis to return competitor, SEO, search query, "
        "service, and audience intelligence."
    )
)
async def analyze_link(request: LinkRequest):
    """
    Main endpoint for website link analysis.
    """
    target_url = str(request.url)
    result = await process_link_analysis(target_url)
    return result
