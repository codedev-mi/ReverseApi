import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.main.linkedin_client.get_profile", new_callable=AsyncMock)
def test_valid_linkedin_url(mock_get_profile):
    mock_get_profile.return_value = {
        "name": "Alex Sharma",
        "headline": "Software Engineer",
        "location": {"name": "Pune, India"},
        "about": "Software engineer interested in backend systems."
    }
    
    valid_urls = [
        "https://www.linkedin.com/in/alexsharma/",
        "https://linkedin.com/in/alexsharma",
        "http://www.linkedin.com/in/alex-sharma-123",
    ]
    for url in valid_urls:
        response = client.post("/api/v1/profile", json={"linkedin_url": url})
        assert response.status_code == 200, f"URL failed validation: {url}"
        data = response.json()
        assert data["success"] is True
        # Check normalized URL format
        expected_username = "alex-sharma-123" if "alex-sharma-123" in url else "alexsharma"
        assert data["profile"]["profile_url"] == f"https://www.linkedin.com/in/{expected_username}/"

def test_invalid_linkedin_url():
    invalid_urls = [
        "https://google.com",
        "https://example.com",
        "not-a-url",
        "",
        "https://www.linkedin.com/company/somecompany",
    ]
    for url in invalid_urls:
        response = client.post("/api/v1/profile", json={"linkedin_url": url})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_LINKEDIN_URL"
        assert "valid LinkedIn profile URL" in data["error"]["message"]
