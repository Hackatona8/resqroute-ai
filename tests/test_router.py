"""Routing tests for ResQRoute AI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.api.schemas import TelemetryPayload
from src.engine.pipeline import TelemetryPipeline


def test_pipeline_flags_escalating_risk_for_hot_follow_up_measurement() -> None:
	pipeline = TelemetryPipeline(risk_threshold=0.35)

	pipeline.ingest(
		TelemetryPayload(
			truck_id="truck-202",
			latitude=19.076,
			longitude=72.8777,
			internal_temp=4.5,
			ambient_temp=27.0,
			cargo_type="fresh_mangoes",
			timestamp=datetime.now(tz=timezone.utc) - timedelta(hours=2),
		)
	)
	result = pipeline.ingest(
		TelemetryPayload(
			truck_id="truck-202",
			latitude=19.082,
			longitude=72.885,
			internal_temp=11.5,
			ambient_temp=36.0,
			cargo_type="fresh_mangoes",
			timestamp=datetime.now(tz=timezone.utc),
		)
	)

	assert result.records_processed == 2
	assert result.risk_score >= 0.0
	assert result.state.value in {"ELEVATED_RISK", "CRITICAL_SPOILAGE_RISK"}
