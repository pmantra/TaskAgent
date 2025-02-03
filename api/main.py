from fastapi import FastAPI
from api.routes import tasks
from api.utils.error_handlers import (
    openai_error_handler,
    auth_error_handler,
    rate_limit_error_handler,
    api_error_handler,
    generic_exception_handler
)
from openai import AuthenticationError, RateLimitError, APIError, OpenAIError

app = FastAPI()

# Include task-related routes
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Register exception handlers
app.add_exception_handler(OpenAIError, openai_error_handler)
app.add_exception_handler(AuthenticationError, auth_error_handler)
app.add_exception_handler(RateLimitError, rate_limit_error_handler)
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/")
def read_root():
    return {"message": "TaskAgent API is running!"}
