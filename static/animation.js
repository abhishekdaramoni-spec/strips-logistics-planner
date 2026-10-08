/**
 * animation.js
 * ============
 * India Geographical Logistics Planning & Real Vector Route Animation Engine
 * Technologies: D3.js v7, GeoJSON (28 States & 8 Union Territories), requestAnimationFrame()
 * Synchronized with: STRIPS State Transitions, Goal-Stack Planning, and Uniform Cost Search (UCS)
 */

// 1. Simulation Runtime State
let indiaGeoData = null;
let projection = null;
let pathGenerator = null;
let nodeProjectedCoords = {}; // code -> [x, y]
let indiaNodesList = [];
let indiaEdgesList = [];
let nodeLookup = {};

let currentPath = ["AMD", "BOM", "JAI"];
let segmentCosts = [2, 2];
let explorationHistory = [];
let totalCost = 4;
let nodesExplored = 4;

let isPlaying = false;
let isPaused = false;
let currentLegIndex = 0;
let progress = 0.0;
let rafId = null;
let activeTimerId = null;
let legStartTime = null;
const legDurationMs = 2200; // 2.2 seconds per flight segment

let currentX = 0;
let currentY = 0;
let currentAngle = 0;
let currentPhase = "READY"; // READY, UCS_SEARCH, TAKEOFF, FLYING, ARRIVED, LANDING, COMPLETED

// 2. Initialize D3 Map & GeoJSON
async function initIndiaMap() {
    const svg = d3.select("#india-map-svg");
    const container = document.getElementById("india-map-container");
    const spinner = document.getElementById("map-loading-spinner");

    const width = 900;
    const height = 950;

    // Load GeoJSON from local static directory
    try {
        indiaGeoData = await d3.json("/static/data/india_states.geojson");
        if (spinner) spinner.style.display = "none";
    } catch (err) {
        console.error("Failed to load local India GeoJSON:", err);
        if (spinner) spinner.innerHTML = `<span style="color:#ef4444;">Failed to load India map data.</span>`;
        return;
    }

    // Read embedded nodes & edges data if present
    const nodesEl = document.getElementById("india-nodes-data");
    const edgesEl = document.getElementById("india-edges-data");
    if (nodesEl) {
        try { indiaNodesList = JSON.parse(nodesEl.textContent); } catch (e) {}
    }
    if (edgesEl) {
        try { indiaEdgesList = JSON.parse(edgesEl.textContent); } catch (e) {}
    }

    // Build lookup dictionary
    indiaNodesList.forEach(node => {
        nodeLookup[node.code] = node;
    });

    // Setup Mercator projection fit to India's GeoJSON geometry
    projection = d3.geoMercator();
    // Fit size with 40px padding
    projection.fitExtent([[30, 30], [width - 30, height - 30]], indiaGeoData);
    pathGenerator = d3.geoPath().projection(projection);

    // Calculate screen coordinates for all airport nodes
    indiaNodesList.forEach(node => {
        const coords = projection([node.lon, node.lat]);
        if (coords) {
            nodeProjectedCoords[node.code] = coords;
        }
    });

    // Clear previous elements
    svg.selectAll("*").remove();

    // 1. Defs: Glow filters and shadows
    const defs = svg.append("defs");
    
    // Cyan Glow Filter
    const filter = defs.append("filter")
        .attr("id", "cyan-glow-filter")
        .attr("x", "-30%").attr("y", "-30%")
        .attr("width", "160%").attr("height", "160%");
    filter.append("feGaussianBlur")
        .attr("stdDeviation", "4")
        .attr("result", "blur");
    filter.append("feComposite")
        .attr("in", "SourceGraphic")
        .attr("in2", "blur")
        .attr("operator", "over");

    // Route Glow Filter
    const routeGlow = defs.append("filter")
        .attr("id", "route-glow-filter")
        .attr("x", "-40%").attr("y", "-40%")
        .attr("width", "180%").attr("height", "180%");
    routeGlow.append("feGaussianBlur")
        .attr("stdDeviation", "5")
        .attr("result", "blur");
    routeGlow.append("feComposite")
        .attr("in", "SourceGraphic")
        .attr("in2", "blur")
        .attr("operator", "over");

    // 2. Base Layers
    const gStates = svg.append("g").attr("class", "layer-states");
    const gRoutes = svg.append("g").attr("class", "layer-routes");
    const gNodes = svg.append("g").attr("class", "layer-nodes");
    const gAirplane = svg.append("g").attr("id", "airplane-layer");

    // 3. Render Real State Boundaries
    gStates.selectAll(".state-boundary")
        .data(indiaGeoData.features)
        .enter()
        .append("path")
        .attr("class", "state-boundary")
        .attr("d", pathGenerator)
        .on("mouseenter", function(event, d) {
            const stateName = d.properties.ST_NM || d.properties.name || "State";
            showTooltip(event, `<strong>${stateName}</strong><br><span class="tip-sub">Indian State / Union Territory</span>`);
        })
        .on("mousemove", function(event) {
            moveTooltip(event);
        })
        .on("mouseleave", function() {
            hideTooltip();
        });

    // Outer India boundary outline glow
    gStates.append("path")
        .datum(indiaGeoData)
        .attr("class", "india-outer-boundary")
        .attr("d", pathGenerator);

    // 4. Render National Flight Routes (Edges)
    indiaEdgesList.forEach(([u, v, cost]) => {
        const p1 = nodeProjectedCoords[u];
        const p2 = nodeProjectedCoords[v];
        if (p1 && p2) {
            gRoutes.append("line")
                .attr("id", `edge-${u}-${v}`)
                .attr("class", "map-route-edge")
                .attr("x1", p1[0]).attr("y1", p1[1])
                .attr("x2", p2[0]).attr("y2", p2[1])
                .attr("data-from", u)
                .attr("data-to", v)
                .attr("data-cost", cost);
        }
    });

    // 5. Render Airport / State Hub Nodes (36 States/UTs + hubs)
    indiaNodesList.forEach(node => {
        const pt = nodeProjectedCoords[node.code];
        if (!pt) return;

        const isCoreDemo = node.is_core;
        const gNode = gNodes.append("g")
            .attr("id", `node-${node.code}`)
            .attr("class", `map-airport-node ${isCoreDemo ? 'node-core-hub' : ''}`)
            .attr("transform", `translate(${pt[0]}, ${pt[1]})`)
            .on("click", () => inspectStateNode(node))
            .on("mouseenter", (event) => {
                showTooltip(event, `
                    <strong>${node.city} (${node.code})</strong><br>
                    <span class="tip-sub">${node.state} • Capital: ${node.capital}</span><br>
                    <span class="tip-sub">${node.airport_name}</span>
                `);
            })
            .on("mousemove", moveTooltip)
            .on("mouseleave", hideTooltip);

        // Pulse ring
        gNode.append("circle")
            .attr("class", "node-pulse-ring")
            .attr("r", isCoreDemo ? 14 : 10);

        // Outer glow circle
        gNode.append("circle")
            .attr("class", "node-outer-glow")
            .attr("r", isCoreDemo ? 9 : 6);

        // Center electric point
        gNode.append("circle")
            .attr("class", "node-center-point")
            .attr("r", isCoreDemo ? 5.5 : 3.5);

        // Node Label (Short code)
        gNode.append("text")
            .attr("class", `map-node-label ${isCoreDemo ? 'label-highlight' : ''}`)
            .attr("x", 12)
            .attr("y", 3)
            .text(node.code);
    });

    // 6. Create Real Vector Airplane Sprite Layer
    const airplane = gAirplane.append("g")
        .attr("id", "airplane")
        .attr("transform", "translate(0, 0) rotate(0)");

    // Outer glow beacon ring
    airplane.append("circle")
        .attr("cx", 0).attr("cy", 0).attr("r", 20)
        .attr("fill", "rgba(0, 240, 255, 0.25)")
        .attr("stroke", "#00f0ff")
        .attr("stroke-width", "2")
        .attr("stroke-dasharray", "3,3");

    // Soft drop shadow
    airplane.append("ellipse")
        .attr("cx", 2).attr("cy", 5).attr("rx", 14).attr("ry", 7)
        .attr("fill", "rgba(2, 11, 26, 0.6)");

    // High-contrast Airliner Silhouette pointing +X (Right, 0 deg)
    airplane.append("path")
        .attr("d", "M 19,0 L 5,-3.5 L -4,-18 L -9,-18 L -5,-3.5 L -15,-3.5 L -19,-8 L -23,-8 L -20,0 L -23,8 L -19,8 L -15,3.5 L -5,3.5 L -9,18 L -4,18 L 5,3.5 Z")
        .attr("fill", "#020b1a")
        .attr("stroke", "#00f0ff")
        .attr("stroke-width", "2.2")
        .attr("stroke-linejoin", "round");

    // Cockpit Window (cyan)
    airplane.append("ellipse")
        .attr("cx", 11).attr("cy", 0).attr("rx", 3).attr("ry", 1.8)
        .attr("fill", "#38bdf8");

    // Center Red Tail Beacon Light
    airplane.append("circle")
        .attr("cx", -18).attr("cy", 0).attr("r", 2.5)
        .attr("fill", "#ef4444");

    // Setup initial position
    if (currentPath && currentPath.length >= 2) {
        highlightCurrentRoute();
        const startPt = nodeProjectedCoords[currentPath[0]];
        if (startPt) {
            setAirplaneTransform(startPt[0], startPt[1], 0);
        }
    }
}

// 3. Airplane Movement & Geometry
function getAirplaneElement() {
    return document.getElementById("airplane");
}

function setAirplaneTransform(x, y, angleDeg) {
    const plane = getAirplaneElement();
    if (plane) {
        if (plane.style && plane.style.transform) {
            plane.style.transform = "";
        }
        plane.setAttribute("transform", `translate(${x.toFixed(2)}, ${y.toFixed(2)}) rotate(${angleDeg.toFixed(2)})`);
    }

    currentX = x;
    currentY = y;
    currentAngle = angleDeg;

    const dx = document.getElementById("debug-x");
    const dy = document.getElementById("debug-y");
    if (dx) dx.textContent = Math.round(x);
    if (dy) dy.textContent = Math.round(y);
}

function highlightCurrentRoute() {
    if (!currentPath || currentPath.length < 2) return;

    // Reset all route lines
    d3.selectAll(".map-route-edge").classed("route-active", false);

    // Reset all nodes
    d3.selectAll(".map-airport-node")
        .classed("node-origin", false)
        .classed("node-goal", false)
        .classed("node-expanding", false)
        .classed("node-explored", false);

    // Highlight active edges along the route
    for (let i = 0; i < currentPath.length - 1; i++) {
        const u = currentPath[i];
        const v = currentPath[i + 1];
        d3.select(`#edge-${u}-${v}`).classed("route-active", true);
        d3.select(`#edge-${v}-${u}`).classed("route-active", true);
    }

    // Set Origin and Goal nodes
    const origin = currentPath[0];
    const goal = currentPath[currentPath.length - 1];
    d3.select(`#node-${origin}`).classed("node-origin", true);
    d3.select(`#node-${goal}`).classed("node-goal", true);
}

// 4. Flight Execution Engine
function startFlightLeg(legIdx) {
    if (legIdx >= currentPath.length - 1) {
        performLanding();
        return;
    }

    currentLegIndex = legIdx;
    progress = 0.0;
    currentPhase = "FLYING";
    updateButtons();

    const fromCode = currentPath[legIdx];
    const toCode = currentPath[legIdx + 1];
    const fromPt = nodeProjectedCoords[fromCode];
    const toPt = nodeProjectedCoords[toCode];

    if (!fromPt || !toPt) {
        console.error("Missing coordinates for leg:", fromCode, toCode);
        return;
    }

    const dx = toPt[0] - fromPt[0];
    const dy = toPt[1] - fromPt[1];
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;

    updateDebugLeg(fromCode, toCode);
    updateDebugStatus("● RUNNING", "status-running");

    const nodeFrom = nodeLookup[fromCode] || { city: fromCode };
    const nodeTo = nodeLookup[toCode] || { city: toCode };
    const cost = segmentCosts[legIdx] !== undefined ? segmentCosts[legIdx] : 2;

    setLiveStatus(
        `FLIGHT IN PROGRESS (Leg ${legIdx + 1} of ${currentPath.length - 1})`,
        `${fromCode} (${nodeFrom.city}) → ${toCode} (${nodeTo.city})`,
        `Flight Cost: ${cost} | Status: IN AIR`,
        0
    );

    setStripsPredicates([
        `PLANE_IN_AIR`,
        `FUEL_AVAILABLE`,
        `PLANE_AT(${fromCode})`
    ], `FLY(${fromCode},${toCode}) [In Flight]`);

    setAirplaneTransform(fromPt[0], fromPt[1], angle);

    legStartTime = performance.now();
    rafId = requestAnimationFrame(animateStep);

    function animateStep(timestamp) {
        if (!isPlaying || isPaused) return;

        const elapsed = timestamp - legStartTime;
        progress = elapsed / legDurationMs;
        if (progress > 1.0) progress = 1.0;

        const x = fromPt[0] + (toPt[0] - fromPt[0]) * progress;
        const y = fromPt[1] + (toPt[1] - fromPt[1]) * progress;

        setAirplaneTransform(x, y, angle);

        const pct = Math.round(progress * 100);
        updateProgressUI(pct, legIdx);

        if (progress < 1.0) {
            rafId = requestAnimationFrame(animateStep);
        } else {
            handleLegArrival(legIdx);
        }
    }
}

function handleLegArrival(legIdx) {
    currentPhase = "ARRIVED";
    const fromCode = currentPath[legIdx];
    const toCode = currentPath[legIdx + 1];
    const toPt = nodeProjectedCoords[toCode];
    const nodeTo = nodeLookup[toCode] || { city: toCode };

    setAirplaneTransform(toPt[0], toPt[1], currentAngle);
    updateProgressUI(100, legIdx);

    // Pulse node upon arrival
    const nodeEl = d3.select(`#node-${toCode}`);
    nodeEl.classed("node-expanding", true);
    setTimeout(() => nodeEl.classed("node-expanding", false), 600);

    setLiveStatus(
        `TOUCHDOWN / ARRIVAL`,
        `✓ Arrived safely at ${toCode} (${nodeTo.city})`,
        `Leg ${legIdx + 1} Completed`,
        100
    );

    setStripsPredicates([
        `PLANE_IN_AIR`,
        `FUEL_AVAILABLE`,
        `PLANE_AT(${toCode})`
    ], `FLY(${fromCode},${toCode}) [Touchdown]`);

    if (legIdx + 1 < currentPath.length - 1) {
        // Intermediate node arrival: brief pause then proceed
        activeTimerId = setTimeout(() => {
            if (isPlaying && !isPaused) {
                startFlightLeg(legIdx + 1);
            }
        }, 550);
    } else {
        // Reached destination: land
        activeTimerId = setTimeout(() => {
            if (isPlaying && !isPaused) {
                performLanding();
            }
        }, 550);
    }
}

function performTakeoff() {
    currentPhase = "TAKEOFF";
    const startCode = currentPath[0];
    const startPt = nodeProjectedCoords[startCode];
    const nodeStart = nodeLookup[startCode] || { city: startCode };

    if (startPt) {
        setAirplaneTransform(startPt[0], startPt[1], 0);
    }

    setLiveStatus(
        "PHASE 3: TAKEOFF CLEARANCE",
        `Departing from ${startCode} (${nodeStart.city})`,
        `Operator: TAKEOFF(${startCode})`,
        0
    );

    setStripsPredicates([
        `PLANE_IN_AIR`,
        `FUEL_AVAILABLE`,
        `PLANE_AT(${startCode})`
    ], `TAKEOFF(${startCode})`);

    activeTimerId = setTimeout(() => {
        if (isPlaying && !isPaused) {
            startFlightLeg(0);
        }
    }, 600);
}

function performLanding() {
    currentPhase = "LANDING";
    const destCode = currentPath[currentPath.length - 1];
    const destPt = nodeProjectedCoords[destCode];
    const nodeDest = nodeLookup[destCode] || { city: destCode };

    if (destPt) {
        setAirplaneTransform(destPt[0], destPt[1], currentAngle);
    }

    setLiveStatus(
        "PHASE 4: LANDING CLEARANCE",
        `Touching down at ${destCode} (${nodeDest.city})`,
        `Operator: LAND(${destCode})`,
        100
    );

    setStripsPredicates([
        `PLANE_AT(${destCode})`,
        `RUNWAY_CLEAR`,
        `FUEL_AVAILABLE`
    ], `LAND(${destCode})`);

    activeTimerId = setTimeout(() => {
        completeGoal();
    }, 700);
}

function completeGoal() {
    currentPhase = "COMPLETED";
    isPlaying = false;
    isPaused = false;
    updateButtons();
    updateDebugStatus("● COMPLETED", "status-completed");

    const destCode = currentPath[currentPath.length - 1];
    const destPt = nodeProjectedCoords[destCode];
    const nodeDest = nodeLookup[destCode] || { city: destCode };

    setLiveStatus(
        "🎯 GOAL REACHED",
        `Parked at Destination: ${destCode} (${nodeDest.city})`,
        `Total Route Cost: ${totalCost} | UCS Optimal`,
        100
    );

    if (destPt) {
        setAirplaneTransform(destPt[0], destPt[1], currentAngle);
    }

    // Show celebration card
    const modal = document.getElementById("goal-reached-card");
    const details = document.getElementById("goal-details-text");
    const summary = document.getElementById("goal-stats-summary");
    if (modal) {
        if (details) {
            const names = currentPath.map(c => nodeLookup[c] ? nodeLookup[c].city : c).join(" → ");
            details.textContent = `${names} (${currentPath.join(" → ")})`;
        }
        if (summary) {
            summary.innerHTML = `
                <div class="stat-pill"><strong>Total Route Cost:</strong> ${totalCost}</div>
                <div class="stat-pill"><strong>Total Operators:</strong> ${currentPath.length + 1}</div>
                <div class="stat-pill"><strong>Nodes Explored:</strong> ${nodesExplored}</div>
                <div class="stat-pill success"><strong>Status:</strong> ✓ UCS Optimal Route Verified</div>
            `;
        }
        modal.style.display = "flex";
    }
}

// 5. Playback Controls
function startAnimation(immediate = true) {
    if (!currentPath || currentPath.length < 2) return;
    stopAllTimers();
    isPlaying = true;
    isPaused = false;
    currentLegIndex = 0;
    progress = 0.0;
    updateButtons();
    updateDebugStatus("● RUNNING", "status-running");

    const modal = document.getElementById("goal-reached-card");
    if (modal) modal.style.display = "none";

    highlightCurrentRoute();

    const startPt = nodeProjectedCoords[currentPath[0]];
    if (startPt) {
        setAirplaneTransform(startPt[0], startPt[1], 0);
    }

    if (immediate) {
        performTakeoff();
    } else {
        runUcsExploration();
    }
}

function runUcsExploration() {
    currentPhase = "UCS_SEARCH";
    updateDebugStatus("● RUNNING", "status-running");
    setLiveStatus("PHASE 1: UCS EXPLORATION", "Evaluating Priority Queue States...", "Expanding frontier", 0);

    if (!explorationHistory || explorationHistory.length === 0) {
        performTakeoff();
        return;
    }

    let idx = 0;
    function nextStep() {
        if (!isPlaying || isPaused) return;
        if (idx < explorationHistory.length) {
            const step = explorationHistory[idx];
            const nodeEl = d3.select(`#node-${step.airport}`);
            nodeEl.classed("node-expanding", true);
            activeTimerId = setTimeout(() => {
                nodeEl.classed("node-expanding", false).classed("node-explored", true);
                idx++;
                nextStep();
            }, 300);
        } else {
            highlightCurrentRoute();
            performTakeoff();
        }
    }
    nextStep();
}

function pauseAnimation() {
    if (!isPlaying || isPaused) return;
    isPaused = true;
    stopAllTimers();
    updateButtons();
    updateDebugStatus("● PAUSED", "status-paused");
    setLiveStatus("⏸ PAUSED", "Flight frozen at current coordinates", "Click [▶ RESUME] to continue", Math.round(progress * 100));
}

function resumeAnimation() {
    if (!isPlaying || !isPaused) return;
    isPaused = false;
    updateButtons();
    updateDebugStatus("● RUNNING", "status-running");

    if (currentPhase === "FLYING") {
        const fromCode = currentPath[currentLegIndex];
        const toCode = currentPath[currentLegIndex + 1];
        const fromPt = nodeProjectedCoords[fromCode];
        const toPt = nodeProjectedCoords[toCode];
        const dx = toPt[0] - fromPt[0];
        const dy = toPt[1] - fromPt[1];
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;

        legStartTime = performance.now() - (progress * legDurationMs);
        rafId = requestAnimationFrame(animateStep);

        function animateStep(timestamp) {
            if (!isPlaying || isPaused) return;
            const elapsed = timestamp - legStartTime;
            progress = elapsed / legDurationMs;
            if (progress > 1.0) progress = 1.0;

            const x = fromPt[0] + (toPt[0] - fromPt[0]) * progress;
            const y = fromPt[1] + (toPt[1] - fromPt[1]) * progress;

            setAirplaneTransform(x, y, angle);
            const pct = Math.round(progress * 100);
            updateProgressUI(pct, currentLegIndex);

            if (progress < 1.0) {
                rafId = requestAnimationFrame(animateStep);
            } else {
                handleLegArrival(currentLegIndex);
            }
        }
    } else if (currentPhase === "TAKEOFF") {
        startFlightLeg(0);
    } else if (currentPhase === "ARRIVED") {
        startFlightLeg(currentLegIndex + 1);
    } else if (currentPhase === "LANDING") {
        completeGoal();
    }
}

function restartAnimation() {
    stopAllTimers();
    isPlaying = false;
    isPaused = false;
    currentLegIndex = 0;
    progress = 0.0;
    currentPhase = "READY";
    updateButtons();
    updateDebugStatus("● READY", "status-ready");

    const modal = document.getElementById("goal-reached-card");
    if (modal) modal.style.display = "none";

    highlightCurrentRoute();

    const startCode = currentPath[0];
    const startPt = nodeProjectedCoords[startCode];
    const nodeStart = nodeLookup[startCode] || { city: startCode };

    if (startPt) {
        setAirplaneTransform(startPt[0], startPt[1], 0);
    }

    setLiveStatus("READY TO FLY", `Parked at ${startCode} (${nodeStart.city})`, "Click [▶ START] to begin flight", 0);
    setStripsPredicates([
        `PLANE_AT(${startCode})`,
        `RUNWAY_CLEAR`,
        `FUEL_AVAILABLE`
    ], "NONE");

    updateProgressUI(0, 0);
}

function skipNextFlight() {
    if (!isPlaying) return;
    stopAllTimers();

    if (currentPhase === "FLYING" || currentPhase === "TAKEOFF") {
        handleLegArrival(currentLegIndex);
    } else if (currentPhase === "ARRIVED") {
        if (currentLegIndex + 1 < currentPath.length - 1) {
            startFlightLeg(currentLegIndex + 1);
        } else {
            performLanding();
        }
    }
}

function stopAllTimers() {
    if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
    }
    if (activeTimerId) {
        clearTimeout(activeTimerId);
        activeTimerId = null;
    }
}

// 6. State Node Click Inspection (Section 18)
function inspectStateNode(node) {
    const panel = document.getElementById("state-info-panel");
    if (!panel) return;

    document.getElementById("info-state-title").textContent = node.state.toUpperCase();
    document.getElementById("info-state-code").textContent = node.state_code;
    document.getElementById("info-state-capital").textContent = node.capital;
    document.getElementById("info-city-name").textContent = node.city;
    document.getElementById("info-airport-code").textContent = node.code;
    document.getElementById("info-airport-name").textContent = node.airport_name;
    document.getElementById("info-coords").textContent = `${node.lat.toFixed(4)}°N, ${node.lon.toFixed(4)}°E`;

    // Find direct connections
    const connsContainer = document.getElementById("info-connections");
    connsContainer.innerHTML = "";
    const connectedAirports = [];
    indiaEdgesList.forEach(([u, v]) => {
        if (u === node.code) connectedAirports.push(v);
        if (v === node.code) connectedAirports.push(u);
    });

    if (connectedAirports.length > 0) {
        connectedAirports.forEach(c => {
            const span = document.createElement("span");
            span.textContent = c;
            connsContainer.appendChild(span);
        });
    } else {
        connsContainer.innerHTML = `<span style="color:#64748b;">Trunk Route Node</span>`;
    }

    panel.style.display = "block";
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// 7. Tooltip Helpers
function showTooltip(event, htmlContent) {
    const tip = document.getElementById("map-tooltip");
    if (!tip) return;
    tip.innerHTML = htmlContent;
    tip.style.display = "block";
    moveTooltip(event);
}

function moveTooltip(event) {
    const tip = document.getElementById("map-tooltip");
    if (!tip) return;
    const container = document.getElementById("india-map-container").getBoundingClientRect();
    const x = event.clientX - container.left + 14;
    const y = event.clientY - container.top + 14;
    tip.style.left = `${x}px`;
    tip.style.top = `${y}px`;
}

function hideTooltip() {
    const tip = document.getElementById("map-tooltip");
    if (tip) tip.style.display = "none";
}

// 8. UI Status Helpers
function updateButtons() {
    const btnStart = document.getElementById("btn-sim-start");
    const btnPause = document.getElementById("btn-sim-pause");
    const btnResume = document.getElementById("btn-sim-resume");
    const btnRestart = document.getElementById("btn-sim-restart");
    const btnNext = document.getElementById("btn-sim-next");

    if (!btnStart) return;

    if (isPlaying) {
        btnStart.disabled = true;
        btnPause.disabled = isPaused;
        btnResume.disabled = !isPaused;
        btnRestart.disabled = false;
        btnNext.disabled = false;
    } else {
        btnStart.disabled = false;
        btnPause.disabled = true;
        btnResume.disabled = true;
        btnRestart.disabled = false;
        btnNext.disabled = true;
    }
}

function updateDebugStatus(statusText, statusClass) {
    const el = document.getElementById("debug-status");
    if (el) {
        el.textContent = statusText;
        el.className = `debug-pill ${statusClass}`;
    }
}

function updateDebugLeg(fromCode, toCode) {
    const el = document.getElementById("debug-leg");
    if (el) {
        el.textContent = `${fromCode} → ${toCode}`;
    }
}

function setLiveStatus(header, legText, costStatus, progressPct) {
    const headEl = document.getElementById("live-flight-header");
    const legEl = document.getElementById("live-flight-leg");
    const costEl = document.getElementById("live-flight-cost");
    const statusEl = document.getElementById("live-flight-status");
    const pText = document.getElementById("live-progress-text");
    const pBar = document.getElementById("live-progress-bar");

    if (headEl) headEl.textContent = header;
    if (legEl) legEl.textContent = legText;
    if (costEl) costEl.textContent = costStatus;
    if (statusEl) statusEl.textContent = isPaused ? "PAUSED" : (currentPhase === "FLYING" ? "✈ IN AIR" : currentPhase);
    if (pText) pText.textContent = `${progressPct}%`;
    if (pBar) pBar.style.width = `${progressPct}%`;
}

function setStripsPredicates(predicatesList, activeOperator) {
    const opEl = document.getElementById("strips-action-active");
    const listEl = document.getElementById("strips-predicates-list");

    if (opEl) opEl.textContent = activeOperator || "NONE";
    if (listEl) {
        listEl.innerHTML = "";
        predicatesList.forEach(p => {
            const li = document.createElement("li");
            li.className = "predicate-badge true-predicate";
            li.innerHTML = `<span class="icon">✓</span> <code>${p}</code>`;
            listEl.appendChild(li);
        });
    }
}

function updateProgressUI(legPct, legIdx) {
    const pText = document.getElementById("live-progress-text");
    const pBar = document.getElementById("live-progress-bar");
    if (pText) pText.textContent = `${legPct}%`;
    if (pBar) pBar.style.width = `${legPct}%`;

    const totalLegs = Math.max(1, currentPath.length - 1);
    const completedLegs = legIdx + (legPct / 100);
    const overallPct = Math.round((completedLegs / totalLegs) * 100);

    const overallText = document.getElementById("overall-progress-text");
    const overallBar = document.getElementById("overall-progress-bar");
    if (overallText) overallText.textContent = `Flight ${Math.min(legIdx + 1, totalLegs)} of ${totalLegs}`;
    if (overallBar) overallBar.style.width = `${overallPct}%`;
}

// 9. Load Plan Data
function loadPlanData(data) {
    if (!data || !data.path || data.path.length < 2) return;
    currentPath = data.path;
    segmentCosts = data.segment_costs || [];
    explorationHistory = data.exploration_history || [];
    totalCost = data.total_cost || 0;
    nodesExplored = data.nodes_explored_count || (data.exploration_history ? data.exploration_history.length : 0);

    restartAnimation();
}

// 10. Bootstrap on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Initialize Map
    await initIndiaMap();

    // 2. Bind Playback Buttons
    const btnStart = document.getElementById("btn-sim-start");
    const btnPause = document.getElementById("btn-sim-pause");
    const btnResume = document.getElementById("btn-sim-resume");
    const btnRestart = document.getElementById("btn-sim-restart");
    const btnNext = document.getElementById("btn-sim-next");

    if (btnStart) btnStart.addEventListener("click", () => startAnimation(true));
    if (btnPause) btnPause.addEventListener("click", pauseAnimation);
    if (btnResume) btnResume.addEventListener("click", resumeAnimation);
    if (btnRestart) btnRestart.addEventListener("click", restartAnimation);
    if (btnNext) btnNext.addEventListener("click", skipNextFlight);

    // 3. Form Interception for AJAX Live Planning
    const form = document.querySelector(".planning-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const currentAirport = form.current_airport.value;
            const goalAirport = form.goal_airport.value;
            const direction = form.direction.value;
            const algorithm = form.algorithm.value;

            if (currentAirport === goalAirport) {
                alert(`Validation Error: Origin and Destination airports cannot be identical (${currentAirport}).`);
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]');
            const origText = submitBtn.textContent;
            submitBtn.textContent = "⏳ Computing Optimal Route...";
            submitBtn.disabled = true;

            try {
                const response = await fetch("/plan", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: JSON.stringify({
                        current_airport: currentAirport,
                        goal_airport: goalAirport,
                        direction: direction,
                        algorithm: algorithm
                    })
                });

                const data = await response.json();
                if (!data.success) {
                    alert(`Planning Failed: ${data.error}`);
                    return;
                }

                loadPlanData(data);
                startAnimation(false); // start with UCS exploration phase

            } catch (err) {
                console.error("AJAX Planning error, submitting standard form:", err);
                form.submit();
            } finally {
                submitBtn.textContent = origText;
                submitBtn.disabled = false;
            }
        });
    }

    // 4. Initial Plan Bootstrap
    const initialDataEl = document.getElementById("initial-plan-data");
    if (initialDataEl) {
        try {
            const planData = JSON.parse(initialDataEl.textContent);
            if (planData && planData.success) {
                loadPlanData(planData);
                setTimeout(() => {
                    startAnimation(true);
                }, 400);
            }
        } catch (e) {
            console.error("Could not parse initial plan data:", e);
        }
    } else {
        loadPlanData({
            path: ["AMD", "BOM", "JAI"],
            segment_costs: [2, 2],
            total_cost: 4,
            nodes_explored_count: 4
        });
        setTimeout(() => {
            startAnimation(true);
        }, 400);
    }
});
