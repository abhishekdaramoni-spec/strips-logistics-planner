import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, render_template, request, jsonify
from planner import (
    AIRPORTS,
    INDIA_NODES_DATA,
    NODE_LOOKUP,
    FLIGHT_EDGES,
    validate_airport_selection,
    predicate_plane_at
)
from ucs import UniformCostSearch
from strips import GoalStackPlanner

app = Flask(__name__)
ucs_engine = UniformCostSearch()


@app.route("/", methods=["GET"])
def index():
    """Renders the main airport planning dashboard with default AMD -> JAI route simulation."""
    import json
    current_airport = "AMD"
    goal_airport = "JAI"
    direction = "forward"
    algorithm = "ucs"

    ucs_result = ucs_engine.search(current_airport, goal_airport, direction)
    search_origin = ucs_result["search_origin"]
    search_target = ucs_result["search_target"]
    optimal_path = ucs_result["path"]
    segment_costs = ucs_result["segment_costs"]

    goal_stack_planner = GoalStackPlanner(
        start_airport=search_origin,
        goal_airport=search_target,
        airport_path=optimal_path,
        segment_costs=segment_costs
    )
    goal_stack_result = goal_stack_planner.generate_demonstration()

    predicates_info = {
        "current_predicate": predicate_plane_at(search_origin),
        "goal_predicate": predicate_plane_at(search_target)
    }

    response_data = {
        "success": True,
        "path": ucs_result["path"],
        "path_names": ucs_result["path_names"],
        "segment_costs": ucs_result["segment_costs"],
        "total_cost": ucs_result["total_cost"],
        "nodes_explored": ucs_result["nodes_explored_count"],
        "nodes_explored_count": ucs_result["nodes_explored_count"],
        "actions": [a["name"] for a in ucs_result["actions_dict"]],
        "actions_dict": ucs_result["actions_dict"],
        "exploration_history": ucs_result["exploration_history"],
        "visual_segments": ucs_result["visual_segments"],
        "direction": ucs_result["direction"],
        "direction_label": ucs_result["direction_label"],
        "search_origin": search_origin,
        "search_target": search_target,
        "goal_reached": ucs_result["goal_reached"],
        "predicates": predicates_info,
        "goal_stack": goal_stack_result,
        "india_nodes": INDIA_NODES_DATA,
        "flight_edges": FLIGHT_EDGES
    }

    return render_template(
        "index.html",
        airports=AIRPORTS,
        flight_edges=FLIGHT_EDGES,
        india_nodes=INDIA_NODES_DATA,
        json_india_nodes=json.dumps(INDIA_NODES_DATA),
        json_flight_edges=json.dumps(FLIGHT_EDGES),
        current_airport=current_airport,
        goal_airport=goal_airport,
        direction=direction,
        algorithm=algorithm,
        result=ucs_result,
        predicates=predicates_info,
        goal_stack=goal_stack_result,
        json_plan_data=json.dumps(response_data),
        error=None
    )


@app.route("/plan", methods=["POST"])
def plan():
    """
    Handles planning request:
    1. Validates inputs
    2. Runs Uniform Cost Search in specified direction
    3. Runs Goal-Stack Planning demonstration
    4. Renders result template (or returns JSON if requested via AJAX)
    """
    # Accept both Form Data and JSON payloads
    if request.is_json:
        data = request.get_json() or {}
        current_airport = data.get("current_airport", "").strip().upper()
        goal_airport = data.get("goal_airport", "").strip().upper()
        direction = data.get("direction", "forward").strip().lower()
        algorithm = data.get("algorithm", "ucs").strip()
    else:
        current_airport = request.form.get("current_airport", "").strip().upper()
        goal_airport = request.form.get("goal_airport", "").strip().upper()
        direction = request.form.get("direction", "forward").strip().lower()
        algorithm = request.form.get("algorithm", "ucs").strip()

    # Input Validation
    is_valid, error_msg = validate_airport_selection(current_airport, goal_airport)
    if not is_valid:
        if request.is_json:
            return jsonify({"success": False, "error": error_msg}), 400
        return render_template(
            "index.html",
            airports=AIRPORTS,
            flight_edges=FLIGHT_EDGES,
            current_airport=current_airport,
            goal_airport=goal_airport,
            direction=direction,
            algorithm=algorithm,
            result=None,
            goal_stack=None,
            error=error_msg
        )

    # Execute Uniform Cost Search
    ucs_result = ucs_engine.search(
        start_airport=current_airport,
        goal_airport=goal_airport,
        direction=direction
    )

    if not ucs_result["success"]:
        if request.is_json:
            return jsonify({"success": False, "error": ucs_result["error"]}), 404
        return render_template(
            "index.html",
            airports=AIRPORTS,
            flight_edges=FLIGHT_EDGES,
            current_airport=current_airport,
            goal_airport=goal_airport,
            direction=direction,
            algorithm=algorithm,
            result=None,
            goal_stack=None,
            error=ucs_result["error"]
        )

    # Execute Goal-Stack Planning based on the discovered route
    search_origin = ucs_result["search_origin"]
    search_target = ucs_result["search_target"]
    optimal_path = ucs_result["path"]
    segment_costs = ucs_result["segment_costs"]

    goal_stack_planner = GoalStackPlanner(
        start_airport=search_origin,
        goal_airport=search_target,
        airport_path=optimal_path,
        segment_costs=segment_costs
    )
    goal_stack_result = goal_stack_planner.generate_demonstration()

    # Formatted predicates for result display
    predicates_info = {
        "current_predicate": predicate_plane_at(search_origin),
        "goal_predicate": predicate_plane_at(search_target)
    }

    # Structured response matching Section 18
    response_data = {
        "success": True,
        "path": ucs_result["path"],
        "path_names": ucs_result["path_names"],
        "segment_costs": ucs_result["segment_costs"],
        "total_cost": ucs_result["total_cost"],
        "nodes_explored": ucs_result["nodes_explored_count"],
        "nodes_explored_count": ucs_result["nodes_explored_count"],
        "actions": [a["name"] for a in ucs_result["actions_dict"]],
        "actions_dict": ucs_result["actions_dict"],
        "exploration_history": ucs_result["exploration_history"],
        "visual_segments": ucs_result["visual_segments"],
        "direction": ucs_result["direction"],
        "direction_label": ucs_result["direction_label"],
        "search_origin": search_origin,
        "search_target": search_target,
        "goal_reached": ucs_result["goal_reached"],
        "predicates": predicates_info,
        "goal_stack": goal_stack_result,
        "india_nodes": INDIA_NODES_DATA,
        "flight_edges": FLIGHT_EDGES
    }

    wants_json = (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
        or request.form.get("format") == "json"
    )

    if wants_json:
        return jsonify(response_data)

    import json
    return render_template(
        "index.html",
        airports=AIRPORTS,
        flight_edges=FLIGHT_EDGES,
        india_nodes=INDIA_NODES_DATA,
        json_india_nodes=json.dumps(INDIA_NODES_DATA),
        json_flight_edges=json.dumps(FLIGHT_EDGES),
        current_airport=current_airport,
        goal_airport=goal_airport,
        direction=direction,
        algorithm=algorithm,
        result=ucs_result,
        predicates=predicates_info,
        goal_stack=goal_stack_result,
        json_plan_data=json.dumps(response_data),
        error=None
    )


if __name__ == "__main__":
    print("=" * 65)
    print("✈️ Airport Planning System using STRIPS, Goal-Stack & UCS")
    print("Serving on http://127.0.0.1:5000")
    print("Press Ctrl+C to terminate.")
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=True)
