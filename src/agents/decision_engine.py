"""Deterministic flash-intervention decision engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final

from pydantic import BaseModel, Field


class BuyerSignal(BaseModel):
	"""Localized buyer telemetry used to choose the fastest stock absorber."""

	buyer_id: str = Field(min_length=1)
	distance_km: float
	local_demand_score: float
	inventory_turnover_score: float


class InterventionContext(BaseModel):
	"""Structured cargo metadata passed into the agent."""

	cargo_type: str = Field(min_length=1)
	cargo_description: str = Field(min_length=1)
	quantity_tons: float
	hours_remaining: float
	risk_score: float
	route_path: list[str]
	alternative_buyers: list[BuyerSignal]
	base_unit_price: float
	currency: str = "USD"


class PricingLineItem(BaseModel):
	"""Discounted price payload for a buyer-facing offer."""

	sku: str
	buyer_id: str
	quantity_tons: float
	original_unit_price: float
	markdown_percent: int
	discounted_unit_price: float
	original_total_price: float
	discounted_total_price: float


class NotificationPayload(BaseModel):
	"""Webhook-ready notification envelope."""

	event_type: str
	buyer_id: str
	markdown_percent: int
	message: str
	route_path: list[str]
	expires_at: str
	webhook_payload: dict[str, object]


class InterventionDecision(BaseModel):
	"""Structured output emitted by the intervention agent."""

	selected_buyer_id: str
	markdown_percent: int
	modified_pricing: list[PricingLineItem]
	notification: NotificationPayload
	rationale: str


FLASH_DISCOUNT_RULES: Final[list[tuple[float, int]]] = [
	(1.0, 60),
	(2.0, 50),
	(4.0, 40),
	(6.0, 30),
]


@dataclass(slots=True)
class FlashInterventionAgent:
	"""Deterministic agent that mimics a structured LangChain decision layer."""

	agent_name: str = "resqroute-flash-intervention-agent"

	def decide(self, context: InterventionContext) -> InterventionDecision:
		"""Produce a buyer selection, markdown, pricing array, and webhook payload."""

		selected_buyer = self._select_buyer(context.alternative_buyers)
		markdown_percent = self._determine_markdown(context.hours_remaining, context.risk_score)
		pricing_line = self._build_pricing_line(context, selected_buyer.buyer_id, markdown_percent)
		notification = self._build_notification(context, selected_buyer.buyer_id, markdown_percent, pricing_line)

		return InterventionDecision(
			selected_buyer_id=selected_buyer.buyer_id,
			markdown_percent=markdown_percent,
			modified_pricing=[pricing_line],
			notification=notification,
			rationale=self._build_rationale(context, selected_buyer.buyer_id, markdown_percent),
		)

	def decide_json(self, context: InterventionContext) -> dict[str, object]:
		"""Return a JSON-ready dictionary for downstream webhook dispatch."""

		return self.decide(context).model_dump(mode="json")

	def _select_buyer(self, candidates: list[BuyerSignal]) -> BuyerSignal:
		if not candidates:
			raise ValueError("at least one buyer signal is required")

		return max(
			candidates,
			key=lambda candidate: (
				candidate.local_demand_score * 1.25
				+ candidate.inventory_turnover_score * 18.0
				- candidate.distance_km * 0.65
				- len(candidate.buyer_id) * 0.05
			),
		)

	def _determine_markdown(self, hours_remaining: float, risk_score: float) -> int:
		markdown_percent = 15
		for threshold, percent in FLASH_DISCOUNT_RULES:
			if hours_remaining <= threshold:
				markdown_percent = percent
				break

		if risk_score >= 0.9:
			markdown_percent = min(60, markdown_percent + 5)

		return markdown_percent

	def _build_pricing_line(
		self,
		context: InterventionContext,
		buyer_id: str,
		markdown_percent: int,
	) -> PricingLineItem:
		discounted_unit_price = round(context.base_unit_price * (1.0 - markdown_percent / 100.0), 2)
		original_total_price = round(context.base_unit_price * context.quantity_tons, 2)
		discounted_total_price = round(discounted_unit_price * context.quantity_tons, 2)

		return PricingLineItem(
			sku=context.cargo_type,
			buyer_id=buyer_id,
			quantity_tons=context.quantity_tons,
			original_unit_price=round(context.base_unit_price, 2),
			markdown_percent=markdown_percent,
			discounted_unit_price=discounted_unit_price,
			original_total_price=original_total_price,
			discounted_total_price=discounted_total_price,
		)

	def _build_notification(
		self,
		context: InterventionContext,
		buyer_id: str,
		markdown_percent: int,
		pricing_line: PricingLineItem,
	) -> NotificationPayload:
		expires_at = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
		message = (
			f"Flash sale trigger for {context.cargo_description}: "
			f"offer {markdown_percent}% off to {buyer_id} immediately."
		)
		webhook_payload = {
			"buyer_id": buyer_id,
			"cargo_type": context.cargo_type,
			"quantity_tons": context.quantity_tons,
			"risk_score": round(context.risk_score, 3),
			"route_path": context.route_path,
			"pricing": pricing_line.model_dump(mode="json"),
		}

		return NotificationPayload(
			event_type="FLASH_INTERVENTION_TRIGGERED",
			buyer_id=buyer_id,
			markdown_percent=markdown_percent,
			message=message,
			route_path=context.route_path,
			expires_at=expires_at,
			webhook_payload=webhook_payload,
		)

	def _build_rationale(self, context: InterventionContext, buyer_id: str, markdown_percent: int) -> str:
		return (
			f"Selected {buyer_id} because it balances demand pressure and distance; "
			f"applied {markdown_percent}% markdown for a {context.hours_remaining:.1f} hour spoilage window."
		)


flash_intervention_agent = FlashInterventionAgent()
