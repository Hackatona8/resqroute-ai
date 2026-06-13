"""Prompt templates for intervention decision generation."""

from __future__ import annotations

from textwrap import dedent

from src.agents.decision_engine import InterventionContext


AGENT_SYSTEM_PROMPT = dedent(
	"""
	You are the ResQRoute flash-intervention agent.
	Choose the buyer that can absorb perishable cargo fastest.
	Return a structured intervention decision with a deterministic markdown and webhook payload.
	"""
).strip()


def build_intervention_prompt(context: InterventionContext) -> str:
	"""Render a compact operator-facing prompt for logging or LLM adapters."""

	buyer_summary = "; ".join(
		(
			f"{buyer.buyer_id}"
			f"|distance={buyer.distance_km:.1f}km"
			f"|demand={buyer.local_demand_score:.1f}"
			f"|turnover={buyer.inventory_turnover_score:.2f}"
		)
		for buyer in context.alternative_buyers
	)

	return dedent(
		f"""
		Cargo: {context.cargo_description}
		Quantity tons: {context.quantity_tons:.2f}
		Hours remaining: {context.hours_remaining:.2f}
		Risk score: {context.risk_score:.3f}
		Route: {' -> '.join(context.route_path)}
		Candidates: {buyer_summary}
		"""
	).strip()
