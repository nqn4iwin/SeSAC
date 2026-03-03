from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.route.user_routers import router as user_router
from app.exceptions import UserNotFoundError, EmailNotAllowedNameExistsError

app = FastAPI()


@app.exception_handler(EmailNotAllowedNameExistsError)
async def email_not_allowed_handler(
    request: Request, exc: EmailNotAllowedNameExistsError
):
    return JSONResponse(
        status_code=409, content={"error": "Email Not Allowed", "message": str(exc)}
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404, content={"error": "User Not Found", "message": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400, content={"error": "Bad Request", "message": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Exception", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "Something went wrong"},
    )


app.include_router(user_router)


@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI!"}
