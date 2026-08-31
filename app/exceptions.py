class LinkedInAPIException(Exception):
    """Base exception for LinkedIn Profile API"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class InvalidLinkedInURLException(LinkedInAPIException):
    def __init__(self, message: str = "Please provide a valid LinkedIn profile URL."):
        super().__init__("INVALID_LINKEDIN_URL", message, status_code=422)

class AuthenticationException(LinkedInAPIException):
    def __init__(self, message: str = "LinkedIn authorization is unavailable or insufficient for this request."):
        super().__init__("AUTHENTICATION_ERROR", message, status_code=401)

class ProfileNotFoundException(LinkedInAPIException):
    def __init__(self, message: str = "The requested LinkedIn profile was not found."):
        super().__init__("PROFILE_NOT_FOUND", message, status_code=404)

class RateLimitException(LinkedInAPIException):
    def __init__(self, message: str = "LinkedIn request rate limit reached."):
        super().__init__("RATE_LIMITED", message, status_code=429)

class UpstreamException(LinkedInAPIException):
    def __init__(self, message: str = "LinkedIn upstream request failed."):
        super().__init__("UPSTREAM_ERROR", message, status_code=502)

class ParsingException(LinkedInAPIException):
    def __init__(self, message: str = "Failed to parse LinkedIn profile response."):
        super().__init__("PARSING_ERROR", message, status_code=500)

class InternalException(LinkedInAPIException):
    def __init__(self, message: str = "An unexpected internal error occurred."):
        super().__init__("INTERNAL_ERROR", message, status_code=500)
