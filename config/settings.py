"""Application settings for ResQRoute AI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "ResQRoute AI"
    telemetry_risk_threshold: float = 0.72
    reroute_weight_multiplier: float = 1.35
    max_discount_percent: int = 60
    min_discount_percent: int = 15
    default_simulation_ticks: int = 12


settings = Settings()
