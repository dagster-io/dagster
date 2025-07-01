"""JSON response utilities with orjson optimization for browser requests."""

import orjson
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _is_browser_request(request: Request) -> bool:
    """Check if the request is coming from a browser based on User-Agent header."""
    user_agent = request.headers.get("user-agent", "") or ""
    user_agent = user_agent.lower()
    browser_indicators = [
        "mozilla",
        "chrome",
        "safari",
        "firefox",
        "edge",
        "opera",
        "msie",
        "trident",
        "webkit",
        "blink",
        "gecko",
        "browser",
        "internet",
    ]
    return any(indicator in user_agent for indicator in browser_indicators)


class OptimizedJSONResponse(Response):
    """Custom JSONResponse that uses orjson compression for browser requests."""

    def __init__(
        self, content, status_code: int = 200, headers=None, media_type: str = "application/json"
    ):
        super().__init__(
            content=content, status_code=status_code, headers=headers, media_type=media_type
        )

    def render(self, content) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)


def create_json_response(content, request: Request, status_code: int = 200, headers=None):
    """Factory function to create appropriate JSON response based on request type."""
    if _is_browser_request(request):
        return OptimizedJSONResponse(content, status_code=status_code, headers=headers)
    else:
        return JSONResponse(content, status_code=status_code, headers=headers)
