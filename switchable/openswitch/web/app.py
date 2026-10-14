"""FastAPI application factory and middleware configuration."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openswitch.config import settings
from openswitch.models import init_db
from openswitch.obs import init_sentry
from openswitch.web.api import api_router
from openswitch.web.ui import ui_router

logger = logging.getLogger("openswitch.web.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing Open-Switch database tables...")
    await init_db()
    init_sentry()
    if settings.demo_mode:
        from openswitch.security import cleanup_old_demo_data
        await cleanup_old_demo_data(max_age_hours=24)
    yield
    logger.info("Open-Switch server shutdown complete.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Open-Switch",
        description="Autonomous engine to evaluate whether open-weight models can replace closed LLMs.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.openswitch_mode == "local" else ["https://*.tech", "https://*.onrender.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from openswitch.web.session import SessionMiddleware
    app.add_middleware(SessionMiddleware)

    # Mount API and UI routers
    app.include_router(api_router)
    app.include_router(ui_router)

    return app


app = create_app()
