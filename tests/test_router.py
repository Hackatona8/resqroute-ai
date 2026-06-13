"""Routing tests for ResQRoute AI."""

from __future__ import annotations

from src.api.schemas import CargoState
from src.engine.router import DynamicRoutingEngine


def test_router_prefers_original_destination_when_cargo_is_stable() -> None:
	engine = DynamicRoutingEngine()

	decision = engine.recalculate_optimal_path(
		current_node="farm_gate",
		original_destination="regional_market",
		cargo_status=CargoState.NORMAL,
	)

	assert decision.rerouted is False
	assert decision.destination == "regional_market"
	assert decision.path[0] == "farm_gate"
	assert decision.path[-1] == "regional_market"


def test_router_reroutes_to_nearest_alternative_buyer_when_critical() -> None:
	engine = DynamicRoutingEngine()

	decision = engine.recalculate_optimal_path(
		current_node="farm_gate",
		original_destination="regional_market",
		cargo_status=CargoState.CRITICAL_SPOILAGE_RISK,
	)

	assert decision.rerouted is True
	assert decision.destination in {"hub_north", "hub_central", "micro_hub_east", "buyer_fresh_mart", "buyer_green_coop", "buyer_urban_pop_up"}
	assert decision.destination != "regional_market"
	assert decision.path[0] == "farm_gate"
	assert decision.path[-1] == decision.destination
