"""Telemetry processing pipeline for ResQRoute AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Final

import numpy as np
import pandas as pd

from config.settings import settings
from src.api.schemas import CargoState, TelemetryPayload, TelemetrySubmissionResponse


SAFE_INTERNAL_TEMP_C: Final[float] = 4.0
SAFE_AMBIENT_TEMP_C: Final[float] = 24.0
RISK_NORMALIZER: Final[float] = 7.5
BASE_SAMPLE_WINDOW_HOURS: Final[float] = 0.25


@dataclass(slots=True)
class TelemetryPipeline:
	"""Stateful telemetry processor backed by a Pandas DataFrame."""

	risk_threshold: float = settings.telemetry_risk_threshold
	_lock: Lock = field(default_factory=Lock, init=False, repr=False)
	_records: pd.DataFrame = field(
		default_factory=lambda: pd.DataFrame(
			columns=[
				"truck_id",
				"latitude",
				"longitude",
				"internal_temp",
				"ambient_temp",
				"cargo_type",
				"timestamp",
			]
		),
		init=False,
		repr=False,
	)

	def ingest(self, payload: TelemetryPayload) -> TelemetrySubmissionResponse:
		"""Persist a telemetry packet and recompute the spoilage risk."""

		incoming = pd.DataFrame([payload.model_dump()])
		incoming["timestamp"] = pd.to_datetime(incoming["timestamp"], utc=True)

		with self._lock:
			self._records = pd.concat([self._records, incoming], ignore_index=True)
			truck_frame = self._records[self._records["truck_id"] == payload.truck_id].copy()

		scored_frame = self._score_frame(truck_frame)
		latest_row = scored_frame.iloc[-1]

		return TelemetrySubmissionResponse(
			truck_id=str(latest_row["truck_id"]),
			risk_score=float(latest_row["spoilage_risk"]),
			state=self._resolve_state(float(latest_row["spoilage_risk"])),
			records_processed=int(scored_frame.shape[0]),
		)

	def _score_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
		"""Compute a vectorized spoilage risk profile for a truck."""

		if frame.empty:
			raise ValueError("telemetry frame is empty")

		ordered = frame.sort_values("timestamp").reset_index(drop=True).copy()
		ordered["timestamp"] = pd.to_datetime(ordered["timestamp"], utc=True)
		ordered["internal_temp"] = pd.to_numeric(ordered["internal_temp"], errors="coerce")
		ordered["ambient_temp"] = pd.to_numeric(ordered["ambient_temp"], errors="coerce")

		elapsed_hours = (
			ordered["timestamp"].diff().dt.total_seconds().div(3600.0).fillna(BASE_SAMPLE_WINDOW_HOURS)
		)
		exposure_multiplier = np.exp(np.maximum(ordered["internal_temp"] - SAFE_INTERNAL_TEMP_C, 0.0) / 6.0)
		exposure_multiplier *= np.exp(
			np.maximum(ordered["ambient_temp"] - SAFE_AMBIENT_TEMP_C, 0.0) / 12.0
		)

		exposure = exposure_multiplier * elapsed_hours.clip(lower=BASE_SAMPLE_WINDOW_HOURS)
		cumulative_exposure = exposure.cumsum()
		ordered["spoilage_risk"] = 1.0 - np.exp(-cumulative_exposure / RISK_NORMALIZER)
		ordered["spoilage_risk"] = ordered["spoilage_risk"].clip(0.0, 1.0)
		ordered["cargo_state"] = np.where(
			ordered["spoilage_risk"] >= self.risk_threshold,
			CargoState.CRITICAL_SPOILAGE_RISK.value,
			np.where(
				ordered["spoilage_risk"] >= self.risk_threshold * 0.65,
				CargoState.ELEVATED_RISK.value,
				CargoState.NORMAL.value,
			),
		)
		return ordered

	@staticmethod
	def _resolve_state(risk_score: float) -> CargoState:
		if risk_score >= settings.telemetry_risk_threshold:
			return CargoState.CRITICAL_SPOILAGE_RISK
		if risk_score >= settings.telemetry_risk_threshold * 0.65:
			return CargoState.ELEVATED_RISK
		return CargoState.NORMAL


telemetry_pipeline = TelemetryPipeline()
