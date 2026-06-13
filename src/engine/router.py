"""Dynamic routing engine for ResQRoute AI."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import hypot
from typing import Final, Iterable

import networkx as nx

from src.api.schemas import CargoState


class TargetClass(str, Enum):
	"""Node categories used by the logistics graph."""

	HUB = "hub"
	BUYER = "buyer"
	DESTINATION = "destination"


@dataclass(slots=True, frozen=True)
class RouteDecision:
	"""Structured result returned by the routing engine."""

	path: list[str]
	destination: str
	travel_cost: float
	rerouted: bool
	target_class: TargetClass
	cargo_status: CargoState


@dataclass(slots=True)
class DynamicRoutingEngine:
	"""Deterministic logistics graph with dynamic congestion weights."""

	graph: nx.DiGraph = field(default_factory=nx.DiGraph, init=False)

	def __post_init__(self) -> None:
		self.graph = self._build_mock_grid()

	def recalculate_optimal_path(
		self,
		current_node: str,
		original_destination: str,
		cargo_status: CargoState | str,
	) -> RouteDecision:
		"""Return the fastest path, rerouting to a nearer buyer or hub when critical."""

		resolved_status = self._resolve_status(cargo_status)
		self._refresh_dynamic_weights(resolved_status)

		if resolved_status is CargoState.CRITICAL_SPOILAGE_RISK:
			reroute_candidates = self._alternative_targets(original_destination)
			best_decision = self._best_alternative_path(current_node, reroute_candidates, resolved_status)
			if best_decision is not None:
				return best_decision

		fallback_path = self._shortest_path(current_node, original_destination)
		return RouteDecision(
			path=fallback_path,
			destination=original_destination,
			travel_cost=self._path_cost(fallback_path),
			rerouted=False,
			target_class=self._node_target_class(original_destination),
			cargo_status=resolved_status,
		)

	def _build_mock_grid(self) -> nx.DiGraph:
		graph = nx.DiGraph()

		nodes = {
			"farm_gate": (0.0, 0.0, TargetClass.DESTINATION),
			"hub_north": (1.0, 1.0, TargetClass.HUB),
			"hub_central": (2.0, 1.0, TargetClass.HUB),
			"micro_hub_east": (3.0, 2.0, TargetClass.HUB),
			"regional_market": (4.0, 1.0, TargetClass.DESTINATION),
			"buyer_fresh_mart": (2.5, 2.0, TargetClass.BUYER),
			"buyer_green_coop": (4.0, 0.0, TargetClass.BUYER),
			"buyer_urban_pop_up": (5.0, 1.0, TargetClass.BUYER),
		}

		for node_id, (x_coord, y_coord, target_class) in nodes.items():
			graph.add_node(node_id, pos=(x_coord, y_coord), target_class=target_class)

		self._add_bidirectional_edge(graph, "farm_gate", "hub_north")
		self._add_bidirectional_edge(graph, "hub_north", "hub_central")
		self._add_bidirectional_edge(graph, "hub_central", "micro_hub_east")
		self._add_bidirectional_edge(graph, "hub_central", "regional_market")
		self._add_bidirectional_edge(graph, "hub_central", "buyer_fresh_mart")
		self._add_bidirectional_edge(graph, "micro_hub_east", "buyer_urban_pop_up")
		self._add_bidirectional_edge(graph, "regional_market", "buyer_green_coop")
		self._add_bidirectional_edge(graph, "buyer_green_coop", "buyer_urban_pop_up")

		return graph

	def _add_bidirectional_edge(self, graph: nx.DiGraph, left: str, right: str) -> None:
		left_pos = graph.nodes[left]["pos"]
		right_pos = graph.nodes[right]["pos"]
		distance = hypot(right_pos[0] - left_pos[0], right_pos[1] - left_pos[1])
		traffic_factor = 1.0 + distance * 0.12
		thermal_penalty = 0.15 + abs(right_pos[1] - left_pos[1]) * 0.08

		graph.add_edge(
			left,
			right,
			base_distance=distance,
			traffic_congestion_factor=traffic_factor,
			ambient_thermal_penalty=thermal_penalty,
			travel_cost=distance,
		)
		graph.add_edge(
			right,
			left,
			base_distance=distance,
			traffic_congestion_factor=traffic_factor,
			ambient_thermal_penalty=thermal_penalty,
			travel_cost=distance,
		)

	def _refresh_dynamic_weights(self, cargo_status: CargoState) -> None:
		for _, _, edge_data in self.graph.edges(data=True):
			base_distance = float(edge_data["base_distance"])
			congestion = float(edge_data["traffic_congestion_factor"])
			thermal_penalty = float(edge_data["ambient_thermal_penalty"])

			if cargo_status is CargoState.CRITICAL_SPOILAGE_RISK:
				edge_data["travel_cost"] = (base_distance * congestion) + (thermal_penalty * 1.8)
			else:
				edge_data["travel_cost"] = (base_distance * 0.92) + (thermal_penalty * 0.5)

	def _alternative_targets(self, original_destination: str) -> list[str]:
		candidates: list[str] = []
		for node_id, node_data in self.graph.nodes(data=True):
			if node_id == original_destination:
				continue
			if node_data.get("target_class") in {TargetClass.HUB, TargetClass.BUYER}:
				candidates.append(node_id)
		return candidates

	def _best_alternative_path(
		self,
		current_node: str,
		candidates: Iterable[str],
		cargo_status: CargoState,
	) -> RouteDecision | None:
		best_decision: RouteDecision | None = None
		for candidate in candidates:
			if not nx.has_path(self.graph, current_node, candidate):
				continue
			path = self._shortest_path(current_node, candidate)
			travel_cost = self._path_cost(path)
			decision = RouteDecision(
				path=path,
				destination=candidate,
				travel_cost=travel_cost,
				rerouted=True,
				target_class=self._node_target_class(candidate),
				cargo_status=cargo_status,
			)
			if best_decision is None or decision.travel_cost < best_decision.travel_cost:
				best_decision = decision
		return best_decision

	def _shortest_path(self, source: str, destination: str) -> list[str]:
		return nx.astar_path(
			self.graph,
			source,
			destination,
			heuristic=self._heuristic,
			weight="travel_cost",
		)

	def _heuristic(self, left: str, right: str) -> float:
		left_pos = self.graph.nodes[left]["pos"]
		right_pos = self.graph.nodes[right]["pos"]
		return hypot(right_pos[0] - left_pos[0], right_pos[1] - left_pos[1])

	def _path_cost(self, path: list[str]) -> float:
		total_cost = 0.0
		for left, right in zip(path, path[1:]):
			total_cost += float(self.graph[left][right]["travel_cost"])
		return total_cost

	def _resolve_status(self, cargo_status: CargoState | str) -> CargoState:
		if isinstance(cargo_status, CargoState):
			return cargo_status
		return CargoState(str(cargo_status))

	def _node_target_class(self, node_id: str) -> TargetClass:
		return self.graph.nodes[node_id]["target_class"]


routing_engine = DynamicRoutingEngine()
