"""Application entry point for ResQRoute AI."""

from __future__ import annotations

from fastapi import FastAPI

from config.settings import settings
from src.api.endpoints import router as telemetry_router


def create_app() -> FastAPI:
	"""Create the FastAPI application."""

	app = FastAPI(title=settings.app_name, version="0.1.0")
	app.include_router(telemetry_router)
	return app


app = create_app()
