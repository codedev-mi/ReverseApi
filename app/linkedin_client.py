import httpx
from typing import Dict, Any
from app.config import settings
from app.exceptions import (
    AuthenticationException,
    ProfileNotFoundException,
    RateLimitException,
    UpstreamException
)
from app.utils import logger

class LinkedInClient:
    def __init__(self):
        self.timeout = settings.request_timeout

    async def get_access_token(self, code: str) -> str:
        """Exchanges authorization code for access token"""
        if not settings.linkedin_client_id or not settings.linkedin_client_secret or not settings.linkedin_redirect_uri:
            logger.error("OAuth client credentials or redirect URI missing in configuration.")
            raise AuthenticationException("OAuth configuration is incomplete on the server.")

        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
            "redirect_uri": settings.linkedin_redirect_uri
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    return token_data["access_token"]
                else:
                    logger.error(f"Failed to exchange code: status {response.status_code}, response: {response.text}")
                    raise AuthenticationException("Failed to obtain access token from LinkedIn.")
            except httpx.RequestError as e:
                logger.error(f"HTTP connection error during token exchange: {str(e)}")
                raise UpstreamException(f"Token exchange connection failed: {str(e)}")

    async def get_profile_by_token(self, token: str) -> Dict[str, Any]:
        """Retrieves user profile info from OIDC endpoint using access token"""
        if token.startswith("mock_"):
            logger.info("Mock token detected, returning mock profile response.")
            return {
                "sub": "auth-member-id",
                "name": "Alex Sharma",
                "given_name": "Alex",
                "family_name": "Sharma",
                "picture": "https://media.licdn.com/dms/image/mock_alex.jpg",
                "locale": {
                    "country": "IN",
                    "language": "en"
                }
            }

        url = "https://api.linkedin.com/v2/userinfo"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                return await self._handle_response(response)
            except httpx.RequestError as e:
                logger.error(f"HTTP connection error to userinfo endpoint: {str(e)}")
                raise UpstreamException(f"Connection to userinfo endpoint failed: {str(e)}")

    async def get_profile(self, profile_url: str) -> Dict[str, Any]:
        """Retrieves profile info using the configured system access token"""
        if not settings.linkedin_access_token:
            logger.error("No default LINKEDIN_ACCESS_TOKEN configured.")
            raise AuthenticationException()
        
        return await self.get_profile_by_token(settings.linkedin_access_token)

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        logger.info(f"LinkedIn upstream response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                raise UpstreamException("Received invalid JSON from LinkedIn.")
        elif response.status_code in (401, 403):
            logger.error("Authentication failed or access denied by LinkedIn upstream.")
            raise AuthenticationException("LinkedIn authorization is unavailable or insufficient for this request.")
        elif response.status_code == 404:
            logger.info("LinkedIn profile not found upstream.")
            raise ProfileNotFoundException()
        elif response.status_code == 429:
            logger.warning("LinkedIn upstream rate limited the request.")
            raise RateLimitException()
        else:
            logger.error(f"LinkedIn upstream returned error code: {response.status_code}")
            raise UpstreamException(f"LinkedIn upstream error: Status {response.status_code}")
