from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.core.config import settings
from app.db.session import sessionmanager
from app.exceptions.exception_handlers import register_exception_handlers
from app.observability.logging import configure_logging, get_logger
from app.observability.middleware import register_middleware
from app.observability.tracing import configure_tracing
from app.routers.private_router import private_router
from app.routers.public_router import public_router

configure_logging(
    settings, log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up application")
    await sessionmanager.init(settings.DATABASE_URL)
    HTTPXClientInstrumentor().instrument()
    yield
    logger.info("Shutting down application")
    await sessionmanager.close()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    FastAPIInstrumentor.instrument_app(app=app)
    configure_tracing(settings=settings)
    register_middleware(app=app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

    app.include_router(public_router)
    app.include_router(private_router)

    register_exception_handlers(app=app)
    return app


app = create_application()
