# LinkedIn Profile API

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0%2B-green)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-enabled-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-quality, browserless HTTPS backend API that retrieves authenticated LinkedIn member information using the official **LinkedIn OpenID Connect (OIDC)** OAuth 2.0 API.

## Overview

This project is a hiring challenge implementation designed to securely handle LinkedIn user profile data. It operates completely browserlessly, using official OAuth 2.0 integration to satisfy security, compliance, and developer guideline criteria.

## Challenge Requirements Implemented

1. **Public HTTPS API**: Ready for cloud platform deployments (Render, Railway, Fly.io) with SSL.
2. **OpenID Connect Authentication**: Uses secure OAuth 2.0 Code Grant flow.
3. **No Browser dependencies**: Absolutely no Selenium, Playwright, Puppeteer, or WebDriver dependencies.
4. **Structured JSON**: Formats responses into normalized Pydantic schemas.
5. **Security First**: Secrets are managed in environment variables, and sensitive headers/tokens are never logged.

## Architecture

```
Client  -->  GET /auth/login  --> Redirect to LinkedIn Auth Screen
                                            │
Client  <--  Redirect back to FastAPI  <────┘ (GET /auth/callback?code=...)
  │
  ├─► POST /api/v1/profile (Passes Bearer Token)
  │
  ▼
FastAPI App
  │
  ├─► HTTPX GET https://api.linkedin.com/v2/userinfo
  │
  ▼
Parser (app/parser.py)
  │
  ├─► Maps name, image, locale -> sets restricted fields to null or []
  │
  ▼
Normalized JSON Response
```

## LinkedIn Developer App Setup & Scopes

To retrieve user profiles, you must configure a LinkedIn Developer Application:
1. Log in to the [LinkedIn Developer Portal](https://developer.linkedin.com/).
2. Create an App and link it to any LinkedIn Company Page.
3. Under the **Products** tab, request access to **Sign In with LinkedIn using OpenID Connect** (approved instantly).
4. Under the **Auth** tab, note your `Client ID` and `Client Secret`.
5. Add your redirect URI (e.g. `http://localhost:8000/auth/callback` or your public production domain callback) to the **Authorized Redirect URLs** list.

### Required Scopes
* `openid`
* `profile`
* `email`

## Environment Variables

All settings are managed via environment variables loaded via Pydantic Settings.

Create a `.env` file in the root directory:
```bash
# LinkedIn OAuth Credentials
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/callback

# (Optional) Pre-configured System Access Token
LINKEDIN_ACCESS_TOKEN=your_oauth_access_token_here

# General Configuration
REQUEST_TIMEOUT=20
LOG_LEVEL=INFO
CORS_ORIGINS=*
```

## Installation & Local Setup

1. Clone the repository and navigate inside:
   ```bash
   git clone https://github.com/your-username/linkedin-profile-api.git
   cd linkedin-profile-api
   ```
2. Create and activate a virtual environment:
   * **Windows**:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   * **Linux/macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your settings:
   ```bash
   cp .env.example .env
   ```
5. Run the server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

The API will run at `http://localhost:8000`.

- Interactive API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative API docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Documentation

### 1. GET `/auth/login`
Redirects the client to the LinkedIn OAuth login page to authenticate and authorize scopes.

### 2. GET `/auth/callback`
Receives the authorization code from LinkedIn, exchanges it for an access token, and returns the token payload:
```json
{
  "success": true,
  "access_token": "EU_...",
  "token_type": "Bearer",
  "scope": "openid profile email"
}
```

### 3. POST `/api/v1/profile`
Fetches and maps profile details. Accepts a token via the `Authorization: Bearer <token>` header or defaults to `LINKEDIN_ACCESS_TOKEN` set in `.env`.
* **Request Body**:
  ```json
  {
    "linkedin_url": "https://www.linkedin.com/in/authenticated-member/"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "success": true,
    "profile": {
      "profile_url": "https://www.linkedin.com/in/authenticated-member/",
      "name": "Alex Sharma",
      "headline": null,
      "location": "IN (en)",
      "about": null,
      "image": "https://media.licdn.com/dms/image/mock_alex.jpg",
      "experience": [],
      "education": [],
      "skills": [],
      "certifications": [],
      "languages": []
    },
    "metadata": {
      "source": "linkedin_oidc",
      "fetched_at": "2026-08-28T20:50:00Z"
    }
  }
  ```

### Curl Example
```bash
curl -X POST \
  http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_oauth_access_token" \
  -d '{"linkedin_url":"https://www.linkedin.com/in/authenticated-member/"}'
```

---

## LinkedIn API Limitations & Field Availability

Because this application communicates directly with LinkedIn's official compliant API endpoints without using web automation or scrapers, it is bound by modern platform privacy permissions:

### Available Fields
* **name**: Retrieved from the standard userinfo OIDC schema (`name`).
* **image**: Retrieved from the `picture` OIDC schema parameter.
* **location**: Mapped from the country/language settings within OIDC `locale`.

### Restricted Fields (Default as `null` or `[]`)
* **headline**, **about**, **experience**, **education**, **skills**, **certifications**, **languages**:
  LinkedIn restricts these fields to verified enterprise partners. Under standard developer OIDC scopes, these return empty.
* **Arbitrary URLs**: Under standard access, you can only retrieve the user profile of the member who completes the OAuth login flow.

---

## Testing

Run tests with `pytest`:
```bash
python -m pytest -v
```

All upstream responses are fully mocked inside `tests/test_profile.py` simulating OIDC responses.

## Docker Setup

### Run with Docker Compose
1. Ensure your `.env` is configured.
2. Build and run:
   ```bash
   docker-compose up --build
   ```

### Run raw Docker commands
1. Build:
   ```bash
   docker build -t linkedin-profile-api .
   ```
2. Run:
   ```bash
   docker run --env-file .env -p 8000:8000 linkedin-profile-api
   ```

## Security Considerations
* **No committed secrets**: `.env` and `*.env` are ignored.
* **Sanitized Logs**: Access tokens, code parameters, and client secrets are never printed to console logs.
* **Middleware protection**: Input parameters are validated via strict Pydantic schemas.
