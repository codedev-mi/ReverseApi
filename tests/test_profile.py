import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.exceptions import AuthenticationException, ProfileNotFoundException, RateLimitException
from app.parser import parse_profile

client = TestClient(app)

MOCK_RAW_RESPONSE = {
    "sub": "auth-member-id",
    "name": "Shruti Bhangale",
    "given_name": "Shruti",
    "family_name": "Bhangale",
    "picture": "https://media.licdn.com/dms/image/mock_shruti.jpg",
    "locale": {
        "country": "IN",
        "language": "en"
    },
    "headline": "Full-Stack Developer | · MERN Stack · Python · AWS | Actively looking Entry-Level Opportunities",
    "about": "Full-stack developer with a strong foundation in React.js, Node.js, Python, C++, and the MERN stack.",
    "experience": [
        {
            "title": "Full Stack Developer Intern",
            "company": "COFA Studio",
            "duration": "7 months",
            "description": "Worked on real-world marketing web products."
        }
    ],
    "education": [
        {
            "school": "K.K. Wagh Institute of Engineering Education & Research",
            "degree": "Master of Computer Applications (MCA)",
            "duration": "2024–2026"
        }
    ],
    "skills": ["React.js", "Node.js", "Python"],
    "certifications": [{"name": "AWS Cloud Foundations"}],
    "languages": [{"language": "English", "proficiency": "Professional working proficiency"}]
}

@patch("app.main.linkedin_client.get_profile_by_token", new_callable=AsyncMock)
@patch("app.main.settings.linkedin_access_token", "mock_system_token")
def test_profile_response_schema(mock_get_profile_by_token):
    mock_get_profile_by_token.return_value = MOCK_RAW_RESPONSE
    
    response = client.post("/api/v1/profile", json={"linkedin_url": "https://www.linkedin.com/in/shrutibhangale/"})
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["profile"]["name"] == "Shruti Bhangale"
    assert data["profile"]["location"] == "IN (en)"
    assert data["profile"]["image"] == "https://media.licdn.com/dms/image/mock_shruti.jpg"
    assert len(data["profile"]["experience"]) == 1
    assert data["profile"]["experience"][0]["company"] == "COFA Studio"
    assert len(data["profile"]["education"]) == 1
    assert len(data["profile"]["skills"]) == 3
    assert len(data["profile"]["certifications"]) == 1
    assert len(data["profile"]["languages"]) == 1
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
    parsed = parse_profile(MOCK_RAW_RESPONSE, "https://www.linkedin.com/in/shrutibhangale/")
    assert parsed["name"] == "Shruti Bhangale"
    assert parsed["location"] == "IN (en)"
    assert parsed["image"] == "https://media.licdn.com/dms/image/mock_shruti.jpg"
    assert len(parsed["experience"]) == 1

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
