# ✈️ Airport Planning System using STRIPS, Goal-Stack Planning and Uniform Cost Search

A beginner-friendly classical Artificial Intelligence planning web application built with **Python**, **Flask**, **HTML**, and **CSS**. Designed for B.Tech AI practical laboratory demonstrations and viva examinations.

---

## 1. Problem Statement & Objective

In classical automated planning, an AI agent must transition from an **Initial State** to a **Goal State** by determining a valid sequence of actions (an *action plan*). 

In an airport/flight domain, an aircraft must travel between airports through a network of flight connections with associated operational costs:
- The aircraft starts parked on a runway (`PLANE_AT(Origin)`).
- It must take off, navigate through intermediate airspace (`PLANE_IN_AIR`), transit through flight legs, and safely touch down at the destination (`PLANE_AT(Destination)`).
- When multiple flight routes exist, the system must determine the **optimal (minimum-cost)** sequence of actions.
- The system must support both **Forward Planning** (Current State → Goal State) and **Reverse Planning** (Goal State → Current State).

---

## 2. Airport World & Flight Network

### Airports (Nodes)
1. **AMD**: Ahmedabad
2. **BOM**: Mumbai
3. **DEL**: Delhi
4. **RAJ**: Rajkot
5. **JAI**: Jaipur

### Connections & Flight Costs (Bidirectional Edges)
| Connection | Cost | Reverse Connection | Cost |
| :--- | :---: | :--- | :---: |
| **AMD ⇄ BOM** | 2 | BOM ⇄ AMD | 2 |
| **BOM ⇄ DEL** | 3 | DEL ⇄ BOM | 3 |
| **AMD ⇄ RAJ** | 2 | RAJ ⇄ AMD | 2 |
| **RAJ ⇄ DEL** | 2 | DEL ⇄ RAJ | 2 |
| **BOM ⇄ JAI** | 2 | JAI ⇄ BOM | 2 |
| **JAI ⇄ DEL** | 2 | DEL ⇄ JAI | 2 |

#### Route Cost Comparison for AMD → DEL:
- **Route 1**: AMD → BOM (2) → DEL (3) = **Total Cost: 5**
- **Route 2 (Optimal)**: AMD → RAJ (2) → DEL (2) = **Total Cost: 4**
- **Route 3**: AMD → BOM (2) → JAI (2) → DEL (2) = **Total Cost: 6**

**Uniform Cost Search (UCS)** evaluates these options and guarantees selecting **Route 2** (Cost = 4).

---

## 3. State Representation (Symbolic Predicates)

States are represented as sets of first-order propositions:
- `PLANE_AT(airport)`: Indicates the plane is physically located at the given airport.
- `RUNWAY_CLEAR`: Indicates the airport runway is clear for takeoff or landing.
- `PLANE_IN_AIR`: Indicates the aircraft is airborne and in transit.
- `FUEL_AVAILABLE`: Indicates sufficient fuel is loaded for flight.

### Initial World State (e.g. Origin AMD)
```prolog
{ PLANE_AT(AMD), RUNWAY_CLEAR, FUEL_AVAILABLE }
```

### Goal State (e.g. Destination DEL)
```prolog
{ PLANE_AT(DEL), RUNWAY_CLEAR }
```

---

## 4. STRIPS Action Representation

STRIPS (*Stanford Research Institute Problem Solver*) represents operators via:
- **Preconditions**: What must be true before the action can occur.
- **Add Effects**: Propositions added to the world state.
- **Delete Effects**: Propositions removed from the world state.
- **Cost**: Numerical cost of executing the action.

### 1. `TAKEOFF(airport)`
- **Preconditions**: `PLANE_AT(airport)`, `RUNWAY_CLEAR`
- **Add Effects**: `PLANE_IN_AIR`
- **Delete Effects**: `RUNWAY_CLEAR`
- **Cost**: `0`

### 2. `FLY(origin, dest)`
- **Preconditions**: `PLANE_IN_AIR`, `PLANE_AT(origin)`, `FUEL_AVAILABLE`
- **Add Effects**: `PLANE_AT(dest)`
- **Delete Effects**: `PLANE_AT(origin)`
- **Cost**: Edge weight from airport network graph (e.g., `2`)

### 3. `LAND(airport)`
- **Preconditions**: `PLANE_IN_AIR`, `PLANE_AT(airport)`
- **Add Effects**: `RUNWAY_CLEAR`
- **Delete Effects**: `PLANE_IN_AIR`
- **Cost**: `0`

---

## 5. Goal-Stack Planning

Goal-Stack Planning is a classical backward-chaining technique:
1. The planner maintains a **LIFO Stack** of goals, sub-goals, and STRIPS operators.
2. The final goal (`PLANE_AT(DEL)`) is pushed onto the stack.
3. The planner inspects the stack top:
   - If it is a predicate already satisfied, it is popped.
   - If it is not satisfied, the planner identifies an operator whose **Add Effects** produce this predicate (e.g., `LAND(DEL)` or `FLY(RAJ,DEL)`).
   - The operator and its preconditions are pushed onto the stack.
4. When an operator reaches the top of the stack and its preconditions are satisfied, it is executed and applied to the world state.
5. The stack unwinds until all goals are achieved.

---

## 6. Uniform Cost Search (UCS)

Uniform Cost Search is implemented from scratch using Python's `heapq` priority queue without third-party graph libraries:
- Explores states in increasing order of path cost $g(n)$.
- Guarantees finding the **optimal (minimum-cost)** flight plan when edge costs are non-negative.
- Supports:
  - **Forward Search**: `Current State → Goal State`
  - **Reverse Search**: `Goal State → Current State` (actually searches from the goal backwards toward the current state).

---

## 7. Real Live SVG Airplane Route Animation

The application features a real, interactive vector simulation powered by SVG and `requestAnimationFrame()`:
1. **Schematic SVG Airport Map**:
   - Exact node coordinates:
     - Ahmedabad (AMD): `(120, 300)`
     - Mumbai (BOM): `(300, 220)`
     - Rajkot (RAJ): `(300, 380)`
     - Delhi (DEL): `(620, 180)`
     - Jaipur (JAI): `(620, 320)`
   - Clearly labeled: *"Schematic airport network — not geographic scale"*
2. **Animation Timeline (Phases 1 to 9)**:
   - **Phase 1: UCS Exploration**: Visualizes priority queue node expansions (orange glowing nodes)
   - **Phase 2: Optimal Route Highlighting**: Highlights computed UCS path edges in glowing indigo
   - **Phase 3: Takeoff**: Updates STRIPS state (`RUNWAY_CLEAR` deleted, `PLANE_IN_AIR` added)
   - **Phase 4+: Flight Segments**: Airplane smoothly interpolates along SVG route lines with dynamic rotation angle
   - **Phase 8: Landing**: Executes `LAND(destination)`
   - **Phase 9: Goal Reached**: Displays completion modal with total cost, actions, and nodes explored
3. **Playback Controls**:
   - `[ ▶ START ]`, `[ ⏸ PAUSE ]`, `[ ▶ RESUME ]`, `[ ↻ RESTART ]`, `[ ⏭ NEXT FLIGHT ]`
4. **Live Panels**:
   - Live Flight Status: Origin, Destination, Leg Cost, Status (`IN AIR`), and Leg Progress bar
   - Live STRIPS State: Dynamic world propositions updated in real time as actions execute

---

## 8. Project File Structure

```
airport-planner/
│
├── app.py              # Flask web server and routing
├── planner.py          # Knowledge base, airport graph, state predicates
├── strips.py           # STRIPS operators and Goal-Stack Planner
├── ucs.py              # Uniform Cost Search using heapq
├── requirements.txt    # Project dependencies (Flask)
├── README.md           # Project documentation and viva guide
│
├── templates/
│   └── index.html      # Frontend HTML template with SVG simulation dashboard
│
└── static/
    ├── style.css       # Clean, modern aviation UI styling
    └── animation.js    # Real-time SVG flight animation engine (requestAnimationFrame)
```

---

## 9. How to Run the Application

### Step 1: Install Requirements
Open PowerShell / Command Prompt and run:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Flask Server
```bash
python app.py
```

### Step 3: Open in Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 9. Example Runs & Outputs

### Example 1: Forward Planning (AMD → DEL)
- **Current State**: `PLANE_AT(AMD)`
- **Goal State**: `PLANE_AT(DEL)`
- **Direction**: Current State → Goal State
- **Optimal Plan**:
  1. `TAKEOFF(AMD)` (Cost: 0)
  2. `FLY(AMD,RAJ)` (Cost: 2)
  3. `FLY(RAJ,DEL)` (Cost: 2)
  4. `LAND(DEL)` (Cost: 0)
- **Total Cost**: `4` (Cheaper than AMD → BOM → DEL which costs 5)
- **Goal Reached**: `YES ✓`

### Example 2: Reverse Planning (DEL → AMD)
- **Direction**: Goal State → Current State
- **Label**: `Reverse Planning: Goal State → Current State`
- **Optimal Plan**:
  1. `TAKEOFF(DEL)` (Cost: 0)
  2. `FLY(DEL,RAJ)` (Cost: 2)
  3. `FLY(RAJ,AMD)` (Cost: 2)
  4. `LAND(AMD)` (Cost: 0)
- **Total Cost**: `4`

### Example 3: Single Leg (AMD → BOM)
- **Optimal Plan**:
  1. `TAKEOFF(AMD)`
  2. `FLY(AMD,BOM)` (Cost: 2)
  3. `LAND(BOM)`
- **Total Cost**: `2`

---

## 10. Viva Questions & Quick Answers

1. **Q: What is STRIPS?**
   *A:* Stanford Research Institute Problem Solver. It represents actions by preconditions, add lists, and delete lists.

2. **Q: Why does UCS guarantee the optimal route?**
   *A:* UCS expands nodes in order of non-decreasing path cost $g(n)$ using a priority queue. Because edge costs are non-negative ($c \ge 0$), the first time the goal node is popped from the queue, its path cost is guaranteed to be minimal.

3. **Q: How does Goal-Stack Planning handle sub-goals?**
   *A:* It uses a LIFO stack. Complex goals are split into sub-goals. Sub-goals that are not yet true in the current state push operators that achieve them onto the stack.
