"""Application entry point for ResQRoute AI."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging

import httpx
from fastapi import FastAPI

from config.settings import settings
from src.agents.decision_engine import BuyerSignal, InterventionContext, flash_intervention_agent
from src.api.endpoints import router as telemetry_router
from src.engine.router import routing_engine


LOGGER = logging.getLogger("resqroute")


def create_app() -> FastAPI:
	"""Create the FastAPI application."""

	app = FastAPI(title=settings.app_name, version="0.1.0")
	app.include_router(telemetry_router)
	return app


app = create_app()


async def run_demo() -> None:
	"""Stream sample telemetry through the API and print reroute decisions."""

	logging.basicConfig(level=logging.INFO, format="%(message)s")

	telemetry_samples = [
		{
			"truck_id": "truck-77",
			"latitude": 17.385,
			"longitude": 78.4867,
			"internal_temp": 4.2,
			"ambient_temp": 29.0,
			"cargo_type": "organic_avocados",
			"timestamp": "2026-06-14T08:00:00Z",
		},
		{
			"truck_id": "truck-77",
			"latitude": 17.3901,
			"longitude": 78.4921,
			"internal_temp": 6.4,
			"ambient_temp": 31.0,
			"cargo_type": "organic_avocados",
			"timestamp": "2026-06-14T09:15:00Z",
		},
		{
			"truck_id": "truck-77",
			"latitude": 17.3982,
			"longitude": 78.5009,
			"internal_temp": 12.6,
			"ambient_temp": 38.0,
			"cargo_type": "organic_avocados",
			"timestamp": "2026-06-14T10:40:00Z",
		},
	]

	transport = httpx.ASGITransport(app=app)
	async with httpx.AsyncClient(transport=transport, base_url="http://resqroute.local") as client:
		latest_response: dict[str, object] | None = None
		for sample in telemetry_samples:
			response = await client.post("/telemetry/submit", json=sample)
			response.raise_for_status()
			latest_response = response.json()
			LOGGER.info("telemetry=%s", json.dumps(latest_response, sort_keys=True))

	if latest_response is None:
		return

	cargo_state = latest_response["state"]
	route_decision = routing_engine.recalculate_optimal_path(
		current_node="farm_gate",
		original_destination="regional_market",
		cargo_status=cargo_state,
	)
	LOGGER.info("route_path=%s", " -> ".join(route_decision.path))

	intervention_context = InterventionContext(
		cargo_type="organic_avocados",
		cargo_description="5 tons of organic avocados",
		quantity_tons=5.0,
		hours_remaining=4.0,
		risk_score=float(latest_response["risk_score"]),
		route_path=route_decision.path,
		alternative_buyers=[
			BuyerSignal(buyer_id="buyer_retail_alpha", distance_km=8.5, local_demand_score=79.0, inventory_turnover_score=0.84),
			BuyerSignal(buyer_id="buyer_urban_pop_up", distance_km=4.2, local_demand_score=91.0, inventory_turnover_score=0.77),
			BuyerSignal(buyer_id="buyer_green_coop", distance_km=6.0, local_demand_score=85.0, inventory_turnover_score=0.81),
		],
		base_unit_price=100.0,
	)
	decision = flash_intervention_agent.decide_json(intervention_context)
	LOGGER.info("decision=%s", json.dumps(decision, sort_keys=True))


def main() -> None:
	"""Start the API server or run the deterministic demo loop."""

	parser = argparse.ArgumentParser(description="Run the ResQRoute AI API or demo harness.")
	parser.add_argument("--demo", action="store_true", help="Run the deterministic telemetry demo and exit.")
	parser.add_argument("--host", default="127.0.0.1", help="Uvicorn host.")
	parser.add_argument("--port", default=8000, type=int, help="Uvicorn port.")
	parser.add_argument("--reload", action="store_true", help="Enable Uvicorn reload mode.")
	args = parser.parse_args()

	if args.demo:
		asyncio.run(run_demo())
		return

	import uvicorn

	uvicorn.run("src.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
	main()
