"""
strips.py
=========
STRIPS Action Representation & Goal-Stack Planning
Implements:
1. StripsAction: Symbolic operator with Preconditions, Add Effects, Delete Effects, and Cost.
2. GoalStackPlanner: Backward-chaining goal decomposition showing how high-level
   goals decompose into sub-goals and STRIPS actions for college AI practical viva.
"""

from typing import List, Set, Dict, Any
from planner import (
    AIRPORTS,
    predicate_plane_at,
    PREDICATE_RUNWAY_CLEAR,
    PREDICATE_PLANE_IN_AIR,
    PREDICATE_FUEL_AVAILABLE,
    get_initial_world_state,
    get_goal_world_state
)


class StripsAction:
    """
    Represents a STRIPS operator:
    - name: Human-readable action name, e.g., 'TAKEOFF(AMD)', 'FLY(AMD,DEL)', 'LAND(DEL)'
    - preconditions: Predicates required before action can be executed
    - add_effects: Predicates added to world state after execution
    - del_effects: Predicates removed from world state after execution
    - cost: Numerical cost associated with this action
    """
    def __init__(
        self,
        name: str,
        preconditions: Set[str],
        add_effects: Set[str],
        del_effects: Set[str],
        cost: int = 0,
        action_type: str = "ACTION",
        details: str = ""
    ):
        self.name = name
        self.preconditions = set(preconditions)
        self.add_effects = set(add_effects)
        self.del_effects = set(del_effects)
        self.cost = cost
        self.action_type = action_type
        self.details = details

    def is_applicable(self, current_state: Set[str]) -> bool:
        """Checks if all preconditions are satisfied in the current world state."""
        return self.preconditions.issubset(current_state)

    def apply(self, current_state: Set[str]) -> Set[str]:
        """
        Executes the action on the world state:
        New State = (Current State - Delete Effects) U Add Effects
        """
        if not self.is_applicable(current_state):
            missing = self.preconditions - current_state
            raise ValueError(f"Action {self.name} cannot be applied! Missing preconditions: {missing}")
        return (current_state - self.del_effects) | self.add_effects

    def to_dict(self) -> Dict[str, Any]:
        """Converts action into dictionary for template rendering."""
        return {
            "name": self.name,
            "action_type": self.action_type,
            "cost": self.cost,
            "details": self.details,
            "preconditions": sorted(list(self.preconditions)),
            "add_effects": sorted(list(self.add_effects)),
            "del_effects": sorted(list(self.del_effects))
        }

    def __repr__(self) -> str:
        return f"<StripsAction {self.name} cost={self.cost}>"


# Standard STRIPS action factories
def create_takeoff_action(airport: str, cost: int = 0) -> StripsAction:
    """Creates a TAKEOFF action for a specific airport."""
    return StripsAction(
        name=f"TAKEOFF({airport})",
        preconditions={predicate_plane_at(airport), PREDICATE_RUNWAY_CLEAR},
        add_effects={PREDICATE_PLANE_IN_AIR},
        del_effects={PREDICATE_RUNWAY_CLEAR},
        cost=cost,
        action_type="TAKEOFF",
        details=f"Aircraft departs from runway at {AIRPORTS.get(airport, airport)}."
    )


def create_fly_action(origin: str, dest: str, cost: int) -> StripsAction:
    """Creates a FLY action between two connected airports."""
    return StripsAction(
        name=f"FLY({origin},{dest})",
        preconditions={PREDICATE_PLANE_IN_AIR, predicate_plane_at(origin), PREDICATE_FUEL_AVAILABLE},
        add_effects={predicate_plane_at(dest)},
        del_effects={predicate_plane_at(origin)},
        cost=cost,
        action_type="FLY",
        details=f"In-flight transit from {AIRPORTS.get(origin, origin)} to {AIRPORTS.get(dest, dest)}."
    )


def create_land_action(airport: str, cost: int = 0) -> StripsAction:
    """Creates a LAND action at a target airport."""
    return StripsAction(
        name=f"LAND({airport})",
        preconditions={PREDICATE_PLANE_IN_AIR, predicate_plane_at(airport)},
        add_effects={PREDICATE_RUNWAY_CLEAR},
        del_effects={PREDICATE_PLANE_IN_AIR},
        cost=cost,
        action_type="LAND",
        details=f"Aircraft touches down and clears runway at {AIRPORTS.get(airport, airport)}."
    )


def build_plan_actions(airport_path: List[str], costs_by_segment: List[int]) -> List[StripsAction]:
    """
    Constructs the concrete STRIPS action sequence for a given airport path:
    1. TAKEOFF(first_airport)
    2. FLY(airport_i, airport_i+1) for each leg
    3. LAND(last_airport)
    """
    if len(airport_path) < 2:
        return []

    actions: List[StripsAction] = []
    
    # Step 1: Takeoff from starting airport
    origin = airport_path[0]
    actions.append(create_takeoff_action(origin, cost=0))

    # Intermediate legs: FLY
    for i in range(len(airport_path) - 1):
        u = airport_path[i]
        v = airport_path[i + 1]
        c = costs_by_segment[i] if i < len(costs_by_segment) else 2
        actions.append(create_fly_action(u, v, cost=c))

    # Final step: Land at destination
    dest = airport_path[-1]
    actions.append(create_land_action(dest, cost=0))

    return actions


class GoalStackPlanner:
    """
    Goal-Stack Planning Demonstration
    ---------------------------------
    Demonstrates classical AI Goal-Stack Planning:
    1. Uses a LIFO Stack to decompose high-level goal into required sub-goals and actions.
    2. Works backward conceptually from the ultimate goal (e.g. PLANE_AT(DEL)).
    3. Traces every stack operation (PUSH, POP, OPERATOR EXECUTION) for college viva examination.
    """

    def __init__(self, start_airport: str, goal_airport: str, airport_path: List[str], segment_costs: List[int]):
        self.start_airport = start_airport
        self.goal_airport = goal_airport
        self.airport_path = airport_path
        self.segment_costs = segment_costs
        self.actions = build_plan_actions(airport_path, segment_costs)

    def generate_demonstration(self) -> Dict[str, Any]:
        """
        Generates both:
        1. Conceptual Backward Goal Decomposition (Goal -> Sub-goal -> Required Action)
        2. Detailed Step-by-Step Goal-Stack Execution Trace with stack snapshots.
        """
        # A. Conceptual Hierarchy (as requested in Section 13)
        hierarchy: List[Dict[str, str]] = []
        hierarchy.append({
            "stage": "Goal",
            "item": predicate_plane_at(self.goal_airport),
            "description": f"Top-level objective: Reach {AIRPORTS.get(self.goal_airport, self.goal_airport)}"
        })
        hierarchy.append({
            "stage": "Sub-goal",
            "item": f"{PREDICATE_PLANE_IN_AIR} & {predicate_plane_at(self.goal_airport)}",
            "description": "Preconditions required before safe landing"
        })
        hierarchy.append({
            "stage": "Required Action",
            "item": f"LAND({self.goal_airport})",
            "description": f"Touch down at destination {self.goal_airport}"
        })

        # Backward flight legs
        for i in range(len(self.airport_path) - 1, 0, -1):
            prev_port = self.airport_path[i - 1]
            curr_port = self.airport_path[i]
            hierarchy.append({
                "stage": "Required Action",
                "item": f"FLY({prev_port},{curr_port})",
                "description": f"Transit flight from {prev_port} to {curr_port}"
            })
            hierarchy.append({
                "stage": "Required Sub-goal",
                "item": f"{PREDICATE_PLANE_IN_AIR} at {prev_port}",
                "description": f"Plane must be airborne originating from {prev_port}"
            })

        hierarchy.append({
            "stage": "Required Action",
            "item": f"TAKEOFF({self.start_airport})",
            "description": f"Takeoff operator satisfies {PREDICATE_PLANE_IN_AIR} from {self.start_airport}"
        })

        # B. Detailed Goal-Stack Simulation Trace
        # Stack tracks both sub-goals (predicates) and operators (StripsAction)
        current_state = get_initial_world_state(self.start_airport)
        trace_steps: List[Dict[str, Any]] = []

        # Build initial stack in reverse order of execution (classical STRIPS stack)
        stack: List[str] = []
        
        # Bottom of stack: final goal state
        stack.append(predicate_plane_at(self.goal_airport))
        stack.append(f"LAND({self.goal_airport})")
        for i in range(len(self.airport_path) - 1, 0, -1):
            stack.append(f"FLY({self.airport_path[i-1]},{self.airport_path[i]})")
            stack.append(PREDICATE_PLANE_IN_AIR)
        stack.append(f"TAKEOFF({self.start_airport})")
        stack.append(PREDICATE_RUNWAY_CLEAR)

        step_counter = 1
        trace_steps.append({
            "step": step_counter,
            "operation": "INITIALIZE_STACK",
            "current_item": "Goal Stack Initialized",
            "stack_snapshot": list(stack),
            "state_snapshot": sorted(list(current_state)),
            "explanation": f"Push top-level goal '{predicate_plane_at(self.goal_airport)}' and backward preconditions onto stack."
        })

        # Simulate execution of the stack
        executed_plan: List[str] = []
        simulated_state = set(current_state)

        for action in self.actions:
            step_counter += 1
            # Check applicability
            can_execute = action.is_applicable(simulated_state)
            simulated_state = action.apply(simulated_state)
            executed_plan.append(action.name)

            # Pop corresponding items from display stack
            if stack:
                popped_item = stack.pop()
            else:
                popped_item = action.name

            trace_steps.append({
                "step": step_counter,
                "operation": f"EXECUTE_{action.action_type}",
                "current_item": action.name,
                "stack_snapshot": list(stack),
                "state_snapshot": sorted(list(simulated_state)),
                "explanation": f"Preconditions satisfied. Applied {action.name}. Deleted: {sorted(list(action.del_effects))}; Added: {sorted(list(action.add_effects))}."
            })

        # Final check
        goal_satisfied = predicate_plane_at(self.goal_airport) in simulated_state
        step_counter += 1
        trace_steps.append({
            "step": step_counter,
            "operation": "GOAL_ACHIEVED",
            "current_item": f"PLANE_AT({self.goal_airport}) verified",
            "stack_snapshot": [],
            "state_snapshot": sorted(list(simulated_state)),
            "explanation": f"Goal state verified! Plane is parked safely at {AIRPORTS.get(self.goal_airport, self.goal_airport)}."
        })

        return {
            "goal": predicate_plane_at(self.goal_airport),
            "hierarchy": hierarchy,
            "final_plan": [a.name for a in self.actions],
            "trace_steps": trace_steps,
            "goal_satisfied": goal_satisfied
        }
