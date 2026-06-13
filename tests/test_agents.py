"""Agent tests for ResQRoute AI."""

from __future__ import annotations

from src.agents.decision_engine import BuyerSignal, InterventionContext, flash_intervention_agent


def test_flash_intervention_agent_selects_best_buyer_and_discount() -> None:
    decision = flash_intervention_agent.decide(
        InterventionContext(
            cargo_type="organic_avocados",
            cargo_description="5 tons of organic avocados",
            quantity_tons=5.0,
            hours_remaining=4.0,
            risk_score=0.91,
            route_path=["farm_gate", "hub_north", "hub_central"],
            alternative_buyers=[
                BuyerSignal(
                    buyer_id="buyer_retail_alpha",
                    distance_km=8.5,
                    local_demand_score=79.0,
                    inventory_turnover_score=0.84,
                ),
                BuyerSignal(
                    buyer_id="buyer_urban_pop_up",
                    distance_km=4.2,
                    local_demand_score=91.0,
                    inventory_turnover_score=0.77,
                ),
            ],
            base_unit_price=100.0,
        )
    )

    assert decision.selected_buyer_id == "buyer_urban_pop_up"
    assert decision.markdown_percent == 45
    assert decision.modified_pricing[0].discounted_unit_price == 55.0
    assert decision.notification.event_type == "FLASH_INTERVENTION_TRIGGERED"
    assert decision.notification.webhook_payload["buyer_id"] == "buyer_urban_pop_up"