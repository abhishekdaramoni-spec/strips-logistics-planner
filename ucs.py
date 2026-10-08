"""
ucs.py
======
Uniform Cost Search (UCS) Implementation from scratch using heapq.
Guarantees finding the minimum-cost route between airports in the network.
Supports both Forward Search (Current -> Goal) and Reverse Search (Goal -> Current).
"""

import heapq
from typing import Dict, List, Tuple, Any, Optional
from planner import FLIGHT_GRAPH, AIRPORTS
from strips import build_plan_actions, StripsAction


class UniformCostSearch:
    """
    Uniform Cost Search (Dijkstra-variant) algorithm.
    Uses Python's heapq priority queue to expand the cheapest path first (g(n)).
    """

    def __init__(self, graph: Dict[str, List[Tuple[str, int]]] = None):
        self.graph = graph if graph is not None else FLIGHT_GRAPH

    def search(
        self,
        start_airport: str,
        goal_airport: str,
        direction: str = "forward"
    ) -> Dict[str, Any]:
        """
        Executes Uniform Cost Search.
        
        Parameters:
        - start_airport: Origin airport code (e.g. 'AMD')
        - goal_airport: Target airport code (e.g. 'DEL')
        - direction: 'forward' (Current -> Goal) or 'reverse' (Goal -> Current)
        
        Returns a dictionary containing:
        - success: bool
        - search_origin: airport where search started
        - search_target: airport where search aimed to reach
        - direction_label: human readable direction label
        - path: list of airport codes
        - path_names: list of airport full names
        - segment_costs: individual flight costs for each leg
        - total_cost: cumulative flight cost
        - nodes_explored_count: number of nodes expanded
        - exploration_history: step-by-step exploration log
        - actions: STRIPS action objects
        - number_of_actions: total count of actions
        """
        # Determine actual search endpoints based on direction
        if direction == "reverse":
            search_start = goal_airport
            search_target = start_airport
            direction_label = "Reverse Planning: Goal State -> Current State"
        else:
            search_start = start_airport
            search_target = goal_airport
            direction_label = "Forward Planning: Current State -> Goal State"

        # Priority Queue holds tuples:
        # (cumulative_cost, tie_breaker_counter, current_airport, path_airports, segment_costs)
        pq: List[Tuple[int, int, str, List[str], List[int]]] = []
        counter = 0

        # Push initial node into Priority Queue
        heapq.heappush(pq, (0, counter, search_start, [search_start], []))

        # Best cost seen so far for each airport
        best_cost: Dict[str, int] = {}

        # Log of explored nodes for educational display
        exploration_history: List[Dict[str, Any]] = []
        nodes_explored_count = 0

        optimal_path: Optional[List[str]] = None
        optimal_segment_costs: Optional[List[int]] = None
        min_total_cost: int = 0
        goal_reached = False

        while pq:
            cost, _, current, path, seg_costs = heapq.heappop(pq)

            # Skip if we already reached this airport with a strictly lower cost
            if current in best_cost and cost > best_cost[current]:
                continue

            best_cost[current] = cost
            nodes_explored_count += 1

            exploration_history.append({
                "step": nodes_explored_count,
                "airport": current,
                "airport_name": AIRPORTS.get(current, current),
                "cumulative_cost": cost,
                "current_path": " -> ".join(path)
            })

            # Goal test
            if current == search_target:
                optimal_path = path
                optimal_segment_costs = seg_costs
                min_total_cost = cost
                goal_reached = True
                break

            # Expand neighbors
            for neighbor, edge_cost in self.graph.get(current, []):
                new_cost = cost + edge_cost
                # If neighbor not visited or found a cheaper path
                if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                    counter += 1
                    new_path = path + [neighbor]
                    new_seg_costs = seg_costs + [edge_cost]
                    heapq.heappush(pq, (new_cost, counter, neighbor, new_path, new_seg_costs))

        if not goal_reached or optimal_path is None:
            return {
                "success": False,
                "error": f"No available flight path found between {search_start} and {search_target}.",
                "search_origin": search_start,
                "search_target": search_target,
                "direction_label": direction_label,
                "nodes_explored_count": nodes_explored_count,
                "exploration_history": exploration_history
            }

        # Build complete STRIPS action sequence
        strips_actions = build_plan_actions(optimal_path, optimal_segment_costs or [])

        # Build visual route segments
        visual_segments: List[Dict[str, Any]] = []
        for i in range(len(optimal_path) - 1):
            u = optimal_path[i]
            v = optimal_path[i + 1]
            c = optimal_segment_costs[i]
            visual_segments.append({
                "from_code": u,
                "from_name": AIRPORTS.get(u, u),
                "to_code": v,
                "to_name": AIRPORTS.get(v, v),
                "action": f"FLY({u},{v})",
                "cost": c
            })

        return {
            "success": True,
            "search_origin": search_start,
            "search_target": search_target,
            "direction": direction,
            "direction_label": direction_label,
            "path": optimal_path,
            "path_names": [AIRPORTS.get(code, code) for code in optimal_path],
            "segment_costs": optimal_segment_costs or [],
            "total_cost": min_total_cost,
            "nodes_explored_count": nodes_explored_count,
            "exploration_history": exploration_history,
            "visual_segments": visual_segments,
            "actions": strips_actions,
            "actions_dict": [a.to_dict() for a in strips_actions],
            "number_of_actions": len(strips_actions),
            "goal_reached": "YES ✓"
        }
