from datetime import datetime, timezone
from fastapi import FastAPI, Request, status, Header
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from typing import Optional

from app.config import settings
from app.exceptions import LinkedInAPIException
from app.schemas import ProfileRequest, ProfileResponse, Profile, Metadata, ErrorResponse, ErrorDetails
from app.linkedin_client import LinkedInClient
from app.parser import parse_profile
from app.utils import setup_logging, logger

setup_logging(settings.log_level)

app = FastAPI(
    title="LinkedIn Profile API",
    description="API for retrieving authorized LinkedIn profile information using OpenID Connect.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS setup
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(LinkedInAPIException)
async def linkedin_api_exception_handler(request: Request, exc: LinkedInAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=ErrorDetails(code=exc.code, message=exc.message)
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    err_msg = "Please provide a valid LinkedIn profile URL."
    if exc.errors():
        err_msg = exc.errors()[0].get("msg", err_msg)
        if "Value error," in err_msg:
            err_msg = err_msg.replace("Value error,", "").strip()

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error=ErrorDetails(code="INVALID_LINKEDIN_URL", message=err_msg)
        ).model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error=ErrorDetails(code="INTERNAL_ERROR", message="An unexpected internal error occurred.")
        ).model_dump()
    )

# Basic Routes
@app.get("/", tags=["general"])
async def read_root():
    return {
        "name": "LinkedIn Profile API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy"
    }

# LinkedIn Client instance
linkedin_client = LinkedInClient()

# OAuth Authentication Endpoints
@app.get("/auth/login", tags=["auth"], summary="Redirect to LinkedIn login")
async def oauth_login():
    if not settings.linkedin_client_id or not settings.linkedin_redirect_uri:
        raise LinkedInAPIException(
            code="AUTHENTICATION_ERROR",
            message="OAuth configuration (LINKEDIN_CLIENT_ID / LINKEDIN_REDIRECT_URI) is missing on the server.",
            status_code=400
        )
    
    url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={settings.linkedin_client_id}&"
        f"redirect_uri={settings.linkedin_redirect_uri}&"
        f"scope=openid%20profile%20email"
    )
    return RedirectResponse(url)

@app.get("/auth/callback", tags=["auth"], summary="OAuth callback receiver")
async def oauth_callback(code: Optional[str] = None, error: Optional[str] = None, error_description: Optional[str] = None):
    if error:
        logger.error(f"OAuth error returned: {error} - {error_description}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                success=False,
                error=ErrorDetails(code="AUTHENTICATION_ERROR", message=f"LinkedIn authorization denied: {error_description}")
            ).model_dump()
        )
    
    if not code:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                success=False,
                error=ErrorDetails(code="AUTHENTICATION_ERROR", message="Missing authorization code.")
            ).model_dump()
        )

    token = await linkedin_client.get_access_token(code)
    return {
        "success": True,
        "access_token": token,
        "token_type": "Bearer",
        "scope": "openid profile email"
    }

# Main endpoint
@app.post(
    "/api/v1/profile",
    response_model=ProfileResponse,
    tags=["profiles"],
    summary="Retrieve LinkedIn profile data",
    description="Accepts a LinkedIn profile URL, fetches OIDC details, and returns structured user profile information."
)
async def get_profile(request: ProfileRequest, authorization: Optional[str] = Header(None)):
    logger.info(f"Request received for profile: {request.linkedin_url}")
    normalized_url = request.linkedin_url
    
    # Resolve authorization token
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif settings.linkedin_access_token:
        token = settings.linkedin_access_token

    if not token:
        logger.error("No access token provided in request headers or server configuration.")
        raise LinkedInAPIException(
            code="AUTHENTICATION_ERROR",
            message="LinkedIn authorization is unavailable or insufficient for this request.",
            status_code=401
        )
        
    logger.info("Profile lookup started")
    raw_data = await linkedin_client.get_profile_by_token(token)
    
    logger.info("Upstream request completed, parsing data")
    try:
        parsed_data = parse_profile(raw_data, normalized_url)
    except Exception as e:
        logger.error(f"Parsing failed: {str(e)}")
        raise LinkedInAPIException(
            code="PARSING_ERROR",
            message="Failed to parse LinkedIn profile response.",
            status_code=500
        )
        
    logger.info("Profile retrieval completed successfully")
    return ProfileResponse(
        success=True,
        profile=Profile(**parsed_data),
        metadata=Metadata(
            source="linkedin_oidc",
            fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    )
