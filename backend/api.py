import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import get_demo_session
from database import DatabaseError, ResourceNotFoundError
from routes.accounts import router as accounts_router
from routes.analytics import router as analytics_router
from routes.csv_imports import router as csv_imports_router
from routes.trades import router as trades_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from rate_limit import limiter


app = FastAPI()


app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service unavailable"},
    )


@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(analytics_router)
app.include_router(csv_imports_router)
app.include_router(trades_router)


@app.get("/")
def root():
    return {"message": "Trading Journal API"}


@app.post("/demo-login")
@limiter.limit("5/minute")
def demo_login(request: Request):
    return get_demo_session()
