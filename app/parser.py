from typing import Dict, Any, List, Optional
from app.utils import logger

def parse_image(data: Dict[str, Any]) -> Optional[str]:
    try:
        return data.get("picture") or None
    except Exception as e:
        logger.warning(f"Error parsing image: {e}")
        return None

def parse_experience(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # OIDC standard access does not return professional experience blocks
    return []

def parse_education(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # OIDC standard access does not return education blocks
    return []

def parse_skills(data: Dict[str, Any]) -> List[str]:
    # OIDC standard access does not return skills
    return []

def parse_certifications(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # OIDC standard access does not return certifications
    return []

def parse_languages(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # OIDC standard access does not return languages
    return []

def parse_profile(data: Dict[str, Any], profile_url: str) -> Dict[str, Any]:
    name = data.get("name")
    if not name:
        first = data.get("given_name", "") or ""
        last = data.get("family_name", "") or ""
        name = f"{first} {last}".strip() or None
    
    # Location resolved from OIDC locale object
    location = None
    locale_data = data.get("locale")
    if isinstance(locale_data, dict):
        country = locale_data.get("country")
        language = locale_data.get("language")
        if country:
            location = country
            if language:
                location = f"{country} ({language})"
    elif isinstance(locale_data, str):
        location = locale_data

    return {
        "profile_url": profile_url,
        "name": name,
        "headline": data.get("headline") or None,
        "location": location,
        "about": data.get("about") or None,
        "image": parse_image(data),
        "experience": parse_experience(data),
        "education": parse_education(data),
        "skills": parse_skills(data),
        "certifications": parse_certifications(data),
        "languages": parse_languages(data)
    }
