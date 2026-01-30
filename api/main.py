import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import router as auth_router
from config import get_settings
from db import init_db
from exceptions import AppException, app_exception_handler, general_exception_handler
from logger import setup_logger
from routes import analytics, email, hyperplanning, integrations, meta, spotify, tasks

settings = get_settings()
logger = setup_logger("main")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info(f"✅ {settings.app_name} v{settings.app_version} started")
    logger.info(f"📊 Database: {settings.database_url}")
    logger.info(f"🔒 Security: Rate limiting enabled ({settings.rate_limit_per_minute}/min)")
    yield
    logger.info(f"🛑 {settings.app_name} stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=()"

    # Performance header
    response.headers["X-Process-Time"] = str(process_time)

    # Logging
    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} ({process_time:.3f}s)"
    )

    return response


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Authentication routes
app.include_router(auth_router)

# API routes
app.include_router(meta.router)
app.include_router(tasks.router)
app.include_router(integrations.router)
app.include_router(hyperplanning.router)
app.include_router(email.router)
app.include_router(spotify.router)
app.include_router(analytics.router)

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    web_path = os.path.join(base_path, "web")
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    web_path = os.path.join(base_path, "..", "web")

if os.path.exists(web_path):
    app.mount("/", StaticFiles(directory=web_path, html=True), name="static")
else:
    logger.warning(f"⚠️ Web directory not found at {web_path}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
