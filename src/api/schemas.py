"""Pydantic schemas for telemetry payloads and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CargoState(str, Enum):
	"""Operational spoilage states used by the telemetry engine."""

	NORMAL = "NORMAL"
	ELEVATED_RISK = "ELEVATED_RISK"
	CRITICAL_SPOILAGE_RISK = "CRITICAL_SPOILAGE_RISK"


class TelemetryPayload(BaseModel):
	"""Incoming IoT telemetry packet for a refrigerated shipment."""

	truck_id: str = Field(min_length=1)
	latitude: float
	longitude: float
	internal_temp: float
	ambient_temp: float
	cargo_type: str = Field(min_length=1)
	timestamp: datetime


class TelemetrySubmissionResponse(BaseModel):
	"""Response emitted after telemetry ingestion and scoring."""

	truck_id: str
	risk_score: float
	state: CargoState
	records_processed: int
