"""
planner.py
===========
Airport Logistics Planning System: India Geographical Knowledge Base & World Model
Includes all 28 Indian States and 8 Union Territories tied to real geographical coordinates (lat/lon).
Retains original core airports (AMD, BOM, DEL, RAJ, JAI) and their flight costs for STRIPS & UCS planning.
"""

from typing import Dict, List, Tuple, Set, Any

# 1. Complete Indian States & Union Territories Geographical Nodes (36 State/UT nodes + Rajkot hub)
# Real latitude and longitude of airport logistics hubs across India
INDIA_NODES_DATA: List[Dict[str, Any]] = [
    # Core Planning Hubs
    {
        "code": "AMD",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "state_code": "GJ",
        "capital": "Gandhinagar",
        "airport_name": "Sardar Vallabhbhai Patel International Airport",
        "lat": 23.0734,
        "lon": 72.6347,
        "is_core": True
    },
    {
        "code": "BOM",
        "city": "Mumbai",
        "state": "Maharashtra",
        "state_code": "MH",
        "capital": "Mumbai",
        "airport_name": "Chhatrapati Shivaji Maharaj International Airport",
        "lat": 19.0896,
        "lon": 72.8656,
        "is_core": True
    },
    {
        "code": "DEL",
        "city": "Delhi",
        "state": "Delhi",
        "state_code": "DL",
        "capital": "New Delhi",
        "airport_name": "Indira Gandhi International Airport",
        "lat": 28.5562,
        "lon": 77.1000,
        "is_core": True
    },
    {
        "code": "RAJ",
        "city": "Rajkot",
        "state": "Gujarat",
        "state_code": "GJ",
        "capital": "Gandhinagar",
        "airport_name": "Rajkot International Airport (Hirasar)",
        "lat": 22.3094,
        "lon": 70.7818,
        "is_core": True
    },
    {
        "code": "JAI",
        "city": "Jaipur",
        "state": "Rajasthan",
        "state_code": "RJ",
        "capital": "Jaipur",
        "airport_name": "Jaipur International Airport",
        "lat": 26.8242,
        "lon": 75.8122,
        "is_core": True
    },

    # Major National Logistics Hubs & Remaining 24 States
    {
        "code": "BLR",
        "city": "Bengaluru",
        "state": "Karnataka",
        "state_code": "KA",
        "capital": "Bengaluru",
        "airport_name": "Kempegowda International Airport",
        "lat": 13.1986,
        "lon": 77.7066,
        "is_core": False
    },
    {
        "code": "MAA",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "state_code": "TN",
        "capital": "Chennai",
        "airport_name": "Chennai International Airport",
        "lat": 12.9941,
        "lon": 80.1709,
        "is_core": False
    },
    {
        "code": "HYD",
        "city": "Hyderabad",
        "state": "Telangana",
        "state_code": "TG",
        "capital": "Hyderabad",
        "airport_name": "Rajiv Gandhi International Airport",
        "lat": 17.2403,
        "lon": 78.4294,
        "is_core": False
    },
    {
        "code": "CCU",
        "city": "Kolkata",
        "state": "West Bengal",
        "state_code": "WB",
        "capital": "Kolkata",
        "airport_name": "Netaji Subhash Chandra Bose International Airport",
        "lat": 22.6547,
        "lon": 88.4467,
        "is_core": False
    },
    {
        "code": "LKO",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "state_code": "UP",
        "capital": "Lucknow",
        "airport_name": "Chaudhary Charan Singh International Airport",
        "lat": 26.7606,
        "lon": 80.8893,
        "is_core": False
    },
    {
        "code": "PNQ",
        "city": "Pune",
        "state": "Maharashtra",
        "state_code": "MH",
        "capital": "Mumbai",
        "airport_name": "Pune Airport",
        "lat": 18.5821,
        "lon": 73.9197,
        "is_core": False
    },
    {
        "code": "GOI",
        "city": "Goa",
        "state": "Goa",
        "state_code": "GA",
        "capital": "Panaji",
        "airport_name": "Dabolim / Manohar International Airport",
        "lat": 15.3808,
        "lon": 73.8314,
        "is_core": False
    },
    {
        "code": "BHO",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "state_code": "MP",
        "capital": "Bhopal",
        "airport_name": "Raja Bhoj Airport",
        "lat": 23.2875,
        "lon": 77.3378,
        "is_core": False
    },
    {
        "code": "PAT",
        "city": "Patna",
        "state": "Bihar",
        "state_code": "BR",
        "capital": "Patna",
        "airport_name": "Jay Prakash Narayan Airport",
        "lat": 25.5913,
        "lon": 85.0880,
        "is_core": False
    },
    {
        "code": "BBI",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "state_code": "OD",
        "capital": "Bhubaneswar",
        "airport_name": "Biju Patnaik Airport",
        "lat": 20.2444,
        "lon": 85.8178,
        "is_core": False
    },
    {
        "code": "RPR",
        "city": "Raipur",
        "state": "Chhattisgarh",
        "state_code": "CG",
        "capital": "Raipur",
        "airport_name": "Swami Vivekananda Airport",
        "lat": 21.1804,
        "lon": 81.7388,
        "is_core": False
    },
    {
        "code": "IXR",
        "city": "Ranchi",
        "state": "Jharkhand",
        "state_code": "JH",
        "capital": "Ranchi",
        "airport_name": "Birsa Munda Airport",
        "lat": 23.3143,
        "lon": 85.3217,
        "is_core": False
    },
    {
        "code": "GAU",
        "city": "Guwahati",
        "state": "Assam",
        "state_code": "AS",
        "capital": "Dispur",
        "airport_name": "Lokpriya Gopinath Bordoloi International Airport",
        "lat": 26.1061,
        "lon": 91.5859,
        "is_core": False
    },
    {
        "code": "VTZ",
        "city": "Visakhapatnam",
        "state": "Andhra Pradesh",
        "state_code": "AP",
        "capital": "Amaravati",
        "airport_name": "Visakhapatnam International Airport",
        "lat": 17.7215,
        "lon": 83.2245,
        "is_core": False
    },
    {
        "code": "COK",
        "city": "Kochi",
        "state": "Kerala",
        "state_code": "KL",
        "capital": "Thiruvananthapuram",
        "airport_name": "Cochin International Airport",
        "lat": 10.1518,
        "lon": 76.3930,
        "is_core": False
    },
    {
        "code": "ATQ",
        "city": "Amritsar",
        "state": "Punjab",
        "state_code": "PB",
        "capital": "Chandigarh",
        "airport_name": "Sri Guru Ram Dass Jee International Airport",
        "lat": 31.7096,
        "lon": 74.7973,
        "is_core": False
    },
    {
        "code": "DED",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "state_code": "UK",
        "capital": "Dehradun",
        "airport_name": "Jolly Grant Airport",
        "lat": 30.1897,
        "lon": 78.1803,
        "is_core": False
    },
    {
        "code": "SLV",
        "city": "Shimla",
        "state": "Himachal Pradesh",
        "state_code": "HP",
        "capital": "Shimla",
        "airport_name": "Shimla Airport",
        "lat": 31.0818,
        "lon": 77.0678,
        "is_core": False
    },
    {
        "code": "PYG",
        "city": "Gangtok",
        "state": "Sikkim",
        "state_code": "SK",
        "capital": "Gangtok",
        "airport_name": "Pakyong Airport",
        "lat": 27.2342,
        "lon": 88.5886,
        "is_core": False
    },
    {
        "code": "IXA",
        "city": "Agartala",
        "state": "Tripura",
        "state_code": "TR",
        "capital": "Agartala",
        "airport_name": "Maharaja Bir Bikram Airport",
        "lat": 23.8869,
        "lon": 91.2405,
        "is_core": False
    },
    {
        "code": "IMF",
        "city": "Imphal",
        "state": "Manipur",
        "state_code": "MN",
        "capital": "Imphal",
        "airport_name": "Bir Tikendrajit International Airport",
        "lat": 24.7600,
        "lon": 93.8967,
        "is_core": False
    },
    {
        "code": "SHL",
        "city": "Shillong",
        "state": "Meghalaya",
        "state_code": "ML",
        "capital": "Shillong",
        "airport_name": "Shillong Airport (Umroi)",
        "lat": 25.7036,
        "lon": 91.9786,
        "is_core": False
    },
    {
        "code": "DMU",
        "city": "Dimapur",
        "state": "Nagaland",
        "state_code": "NL",
        "capital": "Kohima",
        "airport_name": "Dimapur Airport",
        "lat": 25.8839,
        "lon": 93.7711,
        "is_core": False
    },
    {
        "code": "AJL",
        "city": "Aizawl",
        "state": "Mizoram",
        "state_code": "MZ",
        "capital": "Aizawl",
        "airport_name": "Lengpui Airport",
        "lat": 23.8406,
        "lon": 92.6192,
        "is_core": False
    },
    {
        "code": "HGI",
        "city": "Itanagar",
        "state": "Arunachal Pradesh",
        "state_code": "AR",
        "capital": "Itanagar",
        "airport_name": "Donyi Polo Airport (Hollongi)",
        "lat": 26.9944,
        "lon": 93.6522,
        "is_core": False
    },
    {
        "code": "HSS",
        "city": "Hisar",
        "state": "Haryana",
        "state_code": "HR",
        "capital": "Chandigarh",
        "airport_name": "Maharaja Agrasen Airport",
        "lat": 29.1797,
        "lon": 75.7558,
        "is_core": False
    },

    # 8 Union Territories
    {
        "code": "SXR",
        "city": "Srinagar",
        "state": "Jammu & Kashmir",
        "state_code": "JK",
        "capital": "Srinagar",
        "airport_name": "Sheikh ul-Alam International Airport",
        "lat": 33.9871,
        "lon": 74.7742,
        "is_core": False
    },
    {
        "code": "IXL",
        "city": "Leh",
        "state": "Ladakh",
        "state_code": "LA",
        "capital": "Leh",
        "airport_name": "Kushok Bakula Rimpochee Airport",
        "lat": 34.1359,
        "lon": 77.5465,
        "is_core": False
    },
    {
        "code": "IXC",
        "city": "Chandigarh",
        "state": "Chandigarh",
        "state_code": "CH",
        "capital": "Chandigarh",
        "airport_name": "Shaheed Bhagat Singh International Airport",
        "lat": 30.6735,
        "lon": 76.7885,
        "is_core": False
    },
    {
        "code": "IXZ",
        "city": "Port Blair",
        "state": "Andaman & Nicobar",
        "state_code": "AN",
        "capital": "Port Blair",
        "airport_name": "Veer Savarkar International Airport",
        "lat": 11.6414,
        "lon": 92.7297,
        "is_core": False
    },
    {
        "code": "PNY",
        "city": "Puducherry",
        "state": "Puducherry",
        "state_code": "PY",
        "capital": "Puducherry",
        "airport_name": "Puducherry Airport",
        "lat": 11.9680,
        "lon": 79.8105,
        "is_core": False
    },
    {
        "code": "AGX",
        "city": "Agatti",
        "state": "Lakshadweep",
        "state_code": "LD",
        "capital": "Kavaratti",
        "airport_name": "Agatti Aerodrome",
        "lat": 10.8239,
        "lon": 72.1764,
        "is_core": False
    },
    {
        "code": "NMB",
        "city": "Daman",
        "state": "Dadra & Nagar Haveli & Daman & Diu",
        "state_code": "DN",
        "capital": "Daman",
        "airport_name": "Daman Coast Guard Air Station",
        "lat": 20.4344,
        "lon": 72.8428,
        "is_core": False
    }
]

# Dictionary mapping code -> display name (city / state)
AIRPORTS: Dict[str, str] = {node["code"]: node["city"] for node in INDIA_NODES_DATA}
NODE_LOOKUP: Dict[str, Dict[str, Any]] = {node["code"]: node for node in INDIA_NODES_DATA}

# 2. Flight Connections with Costs (Edge weights for Uniform Cost Search)
# PRESERVES ALL ORIGINAL TEST CONNECTIONS AND COSTS EXACTLY:
# AMD ↔ BOM = 2, BOM ↔ DEL = 3, AMD ↔ RAJ = 2, RAJ ↔ DEL = 2, BOM ↔ JAI = 2, JAI ↔ DEL = 2
FLIGHT_EDGES: List[Tuple[str, str, int]] = [
    # Core Historical Network (Strictly preserved for viva tests)
    ("AMD", "BOM", 2),
    ("BOM", "DEL", 3),
    ("AMD", "RAJ", 2),
    ("RAJ", "DEL", 2),
    ("BOM", "JAI", 2),
    ("JAI", "DEL", 2),

    # National Golden Quadrilateral & Trunk Routes
    ("BOM", "PNQ", 1),
    ("BOM", "GOI", 2),
    ("BOM", "BLR", 3),
    ("BOM", "HYD", 3),
    ("BOM", "NMB", 1),
    ("AMD", "NMB", 2),
    ("AMD", "BHO", 3),
    ("BOM", "BHO", 3),

    # Northern Logistics Network
    ("DEL", "LKO", 2),
    ("DEL", "ATQ", 2),
    ("DEL", "IXC", 1),
    ("DEL", "DED", 1),
    ("DEL", "SLV", 2),
    ("DEL", "SXR", 3),
    ("DEL", "HSS", 1),
    ("SXR", "IXL", 2),
    ("DEL", "BHO", 3),
    ("DEL", "PAT", 3),
    ("DEL", "CCU", 4),
    ("DEL", "BLR", 4),
    ("DEL", "HYD", 3),

    # Eastern & Central Network
    ("LKO", "PAT", 2),
    ("PAT", "CCU", 2),
    ("PAT", "IXR", 1),
    ("IXR", "CCU", 2),
    ("IXR", "RPR", 2),
    ("RPR", "BBI", 2),
    ("BHO", "RPR", 2),
    ("CCU", "BBI", 2),
    ("CCU", "GAU", 2),
    ("CCU", "IXZ", 4),

    # Southern Logistics Network
    ("BLR", "MAA", 1),
    ("BLR", "HYD", 2),
    ("BLR", "COK", 2),
    ("MAA", "HYD", 2),
    ("MAA", "PNY", 1),
    ("MAA", "IXZ", 4),
    ("HYD", "VTZ", 2),
    ("BBI", "VTZ", 2),
    ("COK", "AGX", 2),

    # North-Eastern Hub Network (connected through Guwahati)
    ("GAU", "SHL", 1),
    ("GAU", "IMF", 2),
    ("GAU", "DMU", 2),
    ("GAU", "AJL", 2),
    ("GAU", "IXA", 2),
    ("GAU", "HGI", 2),
    ("GAU", "PYG", 2),
]

# Build adjacency graph: airport -> list of (neighbor_airport, flight_cost)
def build_flight_graph() -> Dict[str, List[Tuple[str, int]]]:
    """Constructs a bidirectional adjacency list for the all-India airport network."""
    graph: Dict[str, List[Tuple[str, int]]] = {code: [] for code in AIRPORTS}
    for origin, dest, cost in FLIGHT_EDGES:
        if origin in graph and dest in graph:
            graph[origin].append((dest, cost))
            graph[dest].append((origin, cost))
    return graph

FLIGHT_GRAPH = build_flight_graph()

# 3. Predicate Helper Functions
def predicate_plane_at(airport: str) -> str:
    """Returns the symbolic predicate representing plane location."""
    return f"PLANE_AT({airport})"

PREDICATE_RUNWAY_CLEAR: str = "RUNWAY_CLEAR"
PREDICATE_PLANE_IN_AIR: str = "PLANE_IN_AIR"
PREDICATE_FUEL_AVAILABLE: str = "FUEL_AVAILABLE"

def get_initial_world_state(airport_code: str) -> Set[str]:
    """
    Constructs the initial symbolic state for STRIPS planning.
    Plane is parked at the specified airport, runway is clear, and fuel is ready.
    """
    return {
        predicate_plane_at(airport_code),
        PREDICATE_RUNWAY_CLEAR,
        PREDICATE_FUEL_AVAILABLE
    }

def get_goal_world_state(airport_code: str) -> Set[str]:
    """
    Constructs the target symbolic state for STRIPS planning.
    Plane is safely landed at the goal airport with clear runway.
    """
    return {
        predicate_plane_at(airport_code),
        PREDICATE_RUNWAY_CLEAR
    }

def validate_airport_selection(current_code: str, goal_code: str) -> Tuple[bool, str]:
    """Validates user inputs for current and goal airport selections."""
    if not current_code or not goal_code:
        return False, "Please select both Current and Goal airports."
    
    current_code = current_code.strip().upper()
    goal_code = goal_code.strip().upper()

    if current_code not in AIRPORTS:
        return False, f"Invalid Current airport: '{current_code}'."
    if goal_code not in AIRPORTS:
        return False, f"Invalid Goal airport: '{goal_code}'."
    if current_code == goal_code:
        return False, f"Current airport and Goal airport cannot be identical ({AIRPORTS[current_code]})."
    
    return True, ""
