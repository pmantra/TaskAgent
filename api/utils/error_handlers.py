from fastapi import Request
from fastapi.responses import JSONResponse
from openai import AuthenticationError, RateLimitError, APIError, OpenAIError


async def openai_error_handler(request: Request, exc: OpenAIError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"OpenAI Exception: {str(exc)}"},
    )


async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={"detail": f"OpenAI Authentication Error: {str(exc)}"},
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={"detail": f"OpenAI Rate Limit Exceeded: {str(exc)}"},
    )


async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"OpenAI API Error: {str(exc)}"},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )
