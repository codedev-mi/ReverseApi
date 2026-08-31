import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class ProfileRequest(BaseModel):
    linkedin_url: str

    @field_validator("linkedin_url", mode="before")
    @classmethod
    def validate_and_normalize_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("URL must be a non-empty string.")
        
        v = v.strip()
        # Pattern to match LinkedIn profile URLs (in/username)
        pattern = re.compile(
            r"^https?://(www\.)?linkedin\.com/in/([a-zA-Z0-9_\-%]+)/?.*$",
            re.IGNORECASE
        )
        match = pattern.match(v)
        if not match:
            raise ValueError("Please provide a valid LinkedIn profile URL.")
        
        username = match.group(2)
        return f"https://www.linkedin.com/in/{username}/"

class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

class Language(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None

class Profile(BaseModel):
    profile_url: str
    name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    image: Optional[str] = None
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)

class Metadata(BaseModel):
    source: str = "linkedin"
    fetched_at: str

class ProfileResponse(BaseModel):
    success: bool = True
    profile: Profile
    metadata: Metadata

class ErrorDetails(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails
