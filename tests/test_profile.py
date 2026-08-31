import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.exceptions import AuthenticationException, ProfileNotFoundException, RateLimitException
from app.parser import parse_profile

client = TestClient(app)

MOCK_RAW_RESPONSE = {
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

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_profile_response_schema(mock_get_profile_by_token):
    mock_get_profile_by_token.return_value = MOCK_RAW_RESPONSE
    
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/alexsharma/"})
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["profile"]["name"] == "Alex Sharma"
    assert data["profile"]["location"] == "IN (en)"
    assert data["profile"]["image"] == "https://media.licdn.com/dms/image/mock_alex.jpg"
    assert data["profile"]["experience"] == []
    assert data["profile"]["education"] == []
    assert data["profile"]["skills"] == []
    assert data["profile"]["certifications"] == []
    assert data["profile"]["languages"] == []
    assert "fetched_at" in data["metadata"]
    assert data["metadata"]["source"] == "linkedin_oidc"

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_missing_optional_fields(mock_get_profile_by_token):
    mock_get_profile_by_token.return_value = {
        "given_name": "Minimal",
        "family_name": "User"
    }
    
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/minimal/"})
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["profile"]["name"] == "Minimal User"
    assert data["profile"]["headline"] is None
    assert data["profile"]["location"] is None
    assert data["profile"]["image"] is None
    assert data["profile"]["experience"] == []

def test_parser_with_sample_response():
    parsed = parse_profile(MOCK_RAW_RESPONSE, "https://www.linkedin.com/in/alexsharma/")
    assert parsed["name"] == "Alex Sharma"
    assert parsed["location"] == "IN (en)"
    assert parsed["image"] == "https://media.licdn.com/dms/image/mock_alex.jpg"
    assert parsed["experience"] == []

def test_parser_with_empty_response():
    parsed = parse_profile({}, "https://www.linkedin.com/in/empty/")
    assert parsed["profile_url"] == "https://www.linkedin.com/in/empty/"
    assert parsed["name"] is None
    assert parsed["experience"] == []
    assert parsed["education"] == []

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_upstream_401(mock_get_profile_by_token):
    mock_get_profile_by_token.side_effect = AuthenticationException("LinkedIn authorization is unavailable or insufficient for this request.")
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/alexsharma/"})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_upstream_404(mock_get_profile_by_token):
    mock_get_profile_by_token.side_effect = ProfileNotFoundException()
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/alexsharma/"})
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PROFILE_NOT_FOUND"

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_upstream_429(mock_get_profile_by_token):
    mock_get_profile_by_token.side_effect = RateLimitException()
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/alexsharma/"})
    assert response.status_code == 429
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RATE_LIMITED"
