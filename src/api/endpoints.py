"""FastAPI endpoint definitions for telemetry ingestion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.api.schemas import TelemetryPayload, TelemetrySubmissionResponse
from src.engine.pipeline import TelemetryPipeline, telemetry_pipeline

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def get_pipeline() -> TelemetryPipeline:
	"""Return the shared telemetry pipeline instance."""

	return telemetry_pipeline


@router.post("/submit", response_model=TelemetrySubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_telemetry(
	payload: TelemetryPayload,
	pipeline: TelemetryPipeline = Depends(get_pipeline),
) -> TelemetrySubmissionResponse:
	"""Accept one telemetry packet and return the current spoilage score."""

	return pipeline.ingest(payload)
