"""API tests for ResQRoute AI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.main import app


def test_submit_telemetry_returns_scored_response() -> None:
	client = TestClient(app)
	response = client.post(
		"/telemetry/submit",
		json={
			"truck_id": "truck-101",
			"latitude": 28.6139,
			"longitude": 77.209,
			"internal_temp": 6.5,
			"ambient_temp": 31.0,
			"cargo_type": "organic_avocados",
			"timestamp": (datetime.now(tz=timezone.utc) - timedelta(minutes=15)).isoformat(),
		},
	)

	assert response.status_code == 202
	body = response.json()
	assert body["truck_id"] == "truck-101"
	assert 0.0 <= body["risk_score"] <= 1.0
	assert body["state"] in {
		"NORMAL",
		"ELEVATED_RISK",
		"CRITICAL_SPOILAGE_RISK",
	}
	assert body["records_processed"] == 1
