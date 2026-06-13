"""Interactive Streamlit dashboard for ResQRoute AI Logistics Command Center."""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime, timedelta, timezone
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

# Add root directory to sys.path to enable importing local packages
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.engine.router import routing_engine, TargetClass
from src.agents.decision_engine import flash_intervention_agent, InterventionContext, BuyerSignal
from src.engine.pipeline import TelemetryPipeline, TelemetryPayload, CargoState

# Set page configuration
st.set_page_config(
    page_title="ResQRoute AI Command Center",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom high-tech dark theme styling
st.markdown(
    """
    <style>
    /* Dark dashboard background and custom fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    
    /* Sleek headers and text elements */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    .main-title {
        background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 50%, #6366F1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        display: inline-block;
    }
    
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* High-tech status boxes and components */
    .card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    
    .card-critical {
        border-left: 4px solid #EF4444;
        background: rgba(239, 68, 68, 0.03);
    }
    
    .card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }
    
    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F9FAFB;
    }
    
    /* Custom Streamlit Metrics overrides */
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    /* Staged Badge Elements */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        text-align: center;
    }
    
    .status-normal {
        background-color: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-warning {
        background-color: rgba(245, 158, 11, 0.12);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .status-critical {
        background-color: rgba(239, 68, 68, 0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.25);
        animation: pulse-border 2.5s infinite;
    }
    
    @keyframes pulse-border {
        0% { border-color: rgba(239, 68, 68, 0.4); }
        50% { border-color: rgba(239, 68, 68, 0.8); }
        100% { border-color: rgba(239, 68, 68, 0.4); }
    }
    
    /* Code/JSON Styling */
    .json-code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        background-color: #07090E !important;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1rem;
    }
    
    /* Command center controls */
    .stButton>button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 2rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
    }
    
    .stButton>button:active {
        transform: translateY(1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Geographic Coordinates for Delhi/NCR logistics nodes mapped from the graph
NODE_COORDINATES = {
    "farm_gate": [28.5355, 77.2631],         # Origin
    "hub_north": [28.5855, 77.2231],         # Intermediate
    "hub_central": [28.5655, 77.2931],       # Intermediate
    "micro_hub_east": [28.5955, 77.3431],    # Alternative Hub
    "regional_market": [28.5155, 77.3831],   # Original Destination
    "buyer_fresh_mart": [28.5555, 77.3181],  # Alternative Buyer
    "buyer_green_coop": [28.4955, 77.3231],  # Alternative Buyer
    "buyer_urban_pop_up": [28.5355, 77.3631],# Alternative Buyer
}

# Node types and details for tooltips
NODE_LABELS = {
    "farm_gate": {"name": "Farm Gate Dispatch Terminal", "icon": "warehouse", "color": "blue"},
    "hub_north": {"name": "Logistics Hub North", "icon": "truck", "color": "blue"},
    "hub_central": {"name": "Central Routing Terminal", "icon": "truck", "color": "blue"},
    "micro_hub_east": {"name": "Micro-Hub East", "icon": "building", "color": "orange"},
    "regional_market": {"name": "Regional Market", "icon": "flag", "color": "green"},
    "buyer_fresh_mart": {"name": "FreshMart Retail", "icon": "shopping-cart", "color": "purple"},
    "buyer_green_coop": {"name": "GreenCoop Organics", "icon": "shopping-cart", "color": "purple"},
    "buyer_urban_pop_up": {"name": "Urban Pop-Up Store", "icon": "shopping-cart", "color": "purple"},
}

# API Ingestion Endpoint
API_URL = "http://localhost:8000/telemetry/submit"


def submit_telemetry_payload(payload_dict: dict) -> dict | None:
    """Submit the telemetry payload to the local FastAPI API server.
    
    If the API server is unreachable, returns None to allow local simulation fallback.
    """
    try:
        response = requests.post(API_URL, json=payload_dict, timeout=2.0)
        if response.status_code in (200, 202):
            return response.json()
        else:
            st.error(f"Backend API returned error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException:
        # Fallback will be handled silently
        return None


# Initialize session state variables
if "telemetry_history" not in st.session_state:
    st.session_state.telemetry_history = []

if "sim_time" not in st.session_state:
    # Set standard simulation starting timestamp
    st.session_state.sim_time = datetime.now(timezone.utc) - timedelta(hours=8)

if "local_pipeline" not in st.session_state:
    st.session_state.local_pipeline = TelemetryPipeline()

if "last_response" not in st.session_state:
    st.session_state.last_response = None

# Sidebar Simulation Controls
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <h2 style='margin: 0; color: #38BDF8;'>ResQRoute AI</h2>
        <span style='color: #6B7280; font-size: 0.85rem; font-weight: 600;'>IoT TELEMETRY INJECTOR</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.subheader("Simulation Controls")

# Input fields
truck_id = st.sidebar.text_input("Truck Identifier", value="TRK-902")
cargo_type = st.sidebar.selectbox(
    "Cargo Commodity",
    options=["Avocados", "Strawberries", "Organic Greens", "Fresh Seafood", "Biopharmaceuticals"],
    index=0,
)

# Slider for internal temperature (Crucial to simulate refrigeration failure)
internal_temp = st.sidebar.slider(
    "Internal Cargo Temp (°C)",
    min_value=-5.0,
    max_value=35.0,
    value=4.5,
    step=0.5,
    help="Increase this value to simulate refrigerator compressor malfunction.",
)

# Ambient temperature
ambient_temp = st.sidebar.slider(
    "Ambient Temperature (°C)",
    min_value=15.0,
    max_value=45.0,
    value=35.0,
    step=0.5,
    help="External atmospheric temperature.",
)

# Coordinates matching the current node in the simulated route
# We can dynamically select coordinates based on ticks to simulate movement
route_nodes = ["farm_gate", "hub_north", "hub_central"]
if "route_index" not in st.session_state:
    st.session_state.route_index = 0

current_node = route_nodes[st.session_state.route_index]
base_lat, base_lon = NODE_COORDINATES[current_node]

# Let the user view / tweak GPS telemetry slightly
latitude = st.sidebar.number_input("GPS Latitude", value=base_lat, format="%.5f")
longitude = st.sidebar.number_input("GPS Longitude", value=base_lon, format="%.5f")

st.sidebar.markdown("---")

# Telemetry submission button
inject_triggered = st.sidebar.button(
    "Inject Telemetry Data ⚡",
    use_container_width=True,
    help="Click to submit an IoT telemetry packet and advance simulation by 1 hour.",
)

# Process injection trigger
if inject_triggered:
    # Advance simulated time
    st.session_state.sim_time += timedelta(hours=1)
    
    # Cycle coordinate node indexes to simulate driving along the highway
    st.session_state.route_index = (st.session_state.route_index + 1) % len(route_nodes)
    
    # Construct telemetry payload
    payload = {
        "truck_id": truck_id,
        "latitude": latitude,
        "longitude": longitude,
        "internal_temp": internal_temp,
        "ambient_temp": ambient_temp,
        "cargo_type": cargo_type,
        "timestamp": st.session_state.sim_time.isoformat(),
    }
    
    # 1. Attempt POST call to FastAPI API server
    response_data = submit_telemetry_payload(payload)
    is_api = True
    
    # 2. Fallback to local python pipeline if API is unreachable
    if response_data is None:
        is_api = False
        # Ingest using our duplicated local pipeline state
        try:
            telemetry_payload = TelemetryPayload(
                truck_id=payload["truck_id"],
                latitude=payload["latitude"],
                longitude=payload["longitude"],
                internal_temp=payload["internal_temp"],
                ambient_temp=payload["ambient_temp"],
                cargo_type=payload["cargo_type"],
                timestamp=st.session_state.sim_time,
            )
            local_response = st.session_state.local_pipeline.ingest(telemetry_payload)
            response_data = {
                "truck_id": local_response.truck_id,
                "risk_score": local_response.risk_score,
                "state": local_response.state,
                "records_processed": local_response.records_processed,
            }
        except Exception as e:
            st.error(f"Local simulation ingest failed: {e}")
            
    if response_data:
        st.session_state.last_response = {
            "payload": payload,
            "response": response_data,
            "is_api": is_api,
            "timestamp": st.session_state.sim_time,
        }
        
        # Append to telemetry history for graphing
        st.session_state.telemetry_history.append({
            "timestamp": st.session_state.sim_time,
            "internal_temp": internal_temp,
            "ambient_temp": ambient_temp,
            "risk_score": response_data["risk_score"],
            "state": response_data["state"],
        })

# Header Area
col_logo, col_title = st.columns([1, 12])
with col_title:
    st.markdown("<div class='main-title'>ResQRoute AI Command Center</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Autonomous, data-driven perishable transit logistics dashboard</div>",
        unsafe_allow_html=True,
    )

# Check if we have received at least one telemetry packet
if st.session_state.last_response is None:
    st.info("👋 Welcome to the ResQRoute AI Dashboard! Please click 'Inject Telemetry Data ⚡' in the sidebar to begin the simulation.")
    
    # Render basic baseline map before simulation starts
    m = folium.Map(location=[28.5455, 77.3031], zoom_start=12, tiles="cartodbpositron")
    # Draw original route path
    original_coords = [NODE_COORDINATES[n] for n in ["farm_gate", "hub_north", "hub_central", "regional_market"]]
    folium.PolyLine(original_coords, color="blue", weight=4, opacity=0.85, tooltip="Original Planned Route").add_to(m)
    
    # Add node markers
    for key, coords in NODE_COORDINATES.items():
        label_info = NODE_LABELS.get(key, {"name": key, "color": "blue", "icon": "info-sign"})
        folium.Marker(
            location=coords,
            popup=label_info["name"],
            tooltip=label_info["name"],
            icon=folium.Icon(color=label_info["color"], icon=label_info["icon"], prefix="fa")
        ).add_to(m)
        
    st_folium(m, height=500, use_container_width=True)
    st.stop()

# Retrieve latest data from session state
latest_data = st.session_state.last_response
payload_info = latest_data["payload"]
resp_info = latest_data["response"]
cargo_state_str = resp_info["state"]
risk_score = resp_info["risk_score"]
is_api_connection = latest_data["is_api"]

# Build state color and CSS badges
if cargo_state_str == "NORMAL":
    badge_html = "<span class='status-badge status-normal'>🟢 Normal</span>"
    agent_status_html = "<span class='status-badge status-normal'>Idle</span>"
    agent_status_text = "Idle"
elif cargo_state_str == "ELEVATED_RISK":
    badge_html = "<span class='status-badge status-warning'>🟡 Elevated Risk</span>"
    agent_status_html = "<span class='status-badge status-normal'>Idle</span>"
    agent_status_text = "Idle"
else:  # CRITICAL_SPOILAGE_RISK
    badge_html = "<span class='status-badge status-critical'>🔴 Critical Spoilage Risk</span>"
    agent_status_html = "<span class='status-badge status-critical'>Intervention Active</span>"
    agent_status_text = "Rerouting & Flash Sale Active"

# Top Row Metrics Bar
met_col1, met_col2, met_col3, met_col4 = st.columns(4)

with met_col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🚛 Active Shipment</div>
            <div class="card-value" style="font-size: 1.5rem;">{payload_info['truck_id']}</div>
            <div style="font-size: 0.9rem; color: #9CA3AF; margin-top: 5px;">Cargo: <b>{payload_info['cargo_type']}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with met_col2:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">⚠️ Spoilage Status</div>
            <div style="margin-top: 10px; margin-bottom: 8px;">{badge_html}</div>
            <div style="font-size: 0.9rem; color: #9CA3AF;">Records Processed: <b>{resp_info['records_processed']}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with met_col3:
    # Compute delta risk if available
    delta_risk_str = ""
    if len(st.session_state.telemetry_history) > 1:
        prev_risk = st.session_state.telemetry_history[-2]["risk_score"]
        diff = risk_score - prev_risk
        if diff > 0:
            delta_risk_str = f"📈 +{diff*100:.1f}%"
        elif diff < 0:
            delta_risk_str = f"📉 {diff*100:.1f}%"
            
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">📈 Spoilage Risk Score</div>
            <div class="card-value">{risk_score*100:.1f}%</div>
            <div style="font-size: 0.9rem; color: #EF4444; font-weight: 600;">{delta_risk_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with met_col4:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">🤖 Active Intervention Agent</div>
            <div style="margin-top: 10px; margin-bottom: 8px;">{agent_status_html}</div>
            <div style="font-size: 0.9rem; color: #9CA3AF;">Integration Mode: <b>{"FastAPI Endpoint" if is_api_connection else "Local Simulation"}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Compute optimal routing decision using the backend Python module
# (Keep current_node as hub_central if route index is at the end, or farm_gate, etc.)
decision_current_node = "hub_central" if st.session_state.route_index >= 2 else current_node
route_decision = routing_engine.recalculate_optimal_path(
    current_node=decision_current_node,
    original_destination="regional_market",
    cargo_status=cargo_state_str,
)

# Layout Split: Map (Left) and Decision Panel (Right)
main_left, main_right = st.columns([3, 2])

with main_left:
    st.markdown("### 🗺️ Live Fleet Routing Map")
    
    # Initialize Folium Map around central NCR
    map_center = [28.5455, 77.3031]
    m = folium.Map(location=map_center, zoom_start=11.5, tiles="cartodbpositron")
    
    # Nodes in the original planned route
    original_route_nodes = ["farm_gate", "hub_north", "hub_central", "regional_market"]
    original_coords = [NODE_COORDINATES[n] for n in original_route_nodes]
    
    # Check if a critical reroute occurred
    is_rerouted = route_decision.rerouted and cargo_state_str == "CRITICAL_SPOILAGE_RISK"
    
    if not is_rerouted:
        # Draw full original path in Blue
        folium.PolyLine(
            original_coords,
            color="#2563EB",
            weight=5,
            opacity=0.9,
            tooltip="Active Original Path (Normal)",
        ).add_to(m)
    else:
        # Draw original path in dotted or faded blue/gray to show it was abandoned
        folium.PolyLine(
            original_coords,
            color="#6B7280",
            weight=3,
            opacity=0.4,
            dash_array="5, 10",
            tooltip="Abandoned Route Path",
        ).add_to(m)
        
        # Determine coordinates of the new route
        new_route_nodes = route_decision.path
        
        # Wait, if route_decision.path doesn't start with farm_gate because of current_node,
        # we can stitch the historical driving nodes to the map to draw a full continuous path!
        driving_history_coords = []
        for n in original_route_nodes:
            driving_history_coords.append(NODE_COORDINATES[n])
            if n == decision_current_node:
                break
                
        new_path_coords = [NODE_COORDINATES[n] for n in new_route_nodes]
        full_new_route_coords = driving_history_coords + new_path_coords[1:] if len(new_path_coords) > 1 else new_path_coords
        
        # Draw the active rerouted path in Neon Red
        folium.PolyLine(
            full_new_route_coords,
            color="#EF4444",
            weight=6,
            opacity=0.9,
            tooltip="CRITICAL ALTERNATIVE PATH",
        ).add_to(m)
        
    # Draw markers for all nodes
    for node_name, coords in NODE_COORDINATES.items():
        node_style = NODE_LABELS.get(node_name, {"name": node_name, "color": "blue", "icon": "info-sign"})
        popup_text = f"<b>{node_style['name']}</b><br>Type: {node_name.upper()}"
        
        # Color nodes dynamically depending on if they are active, bypassed, or target destinations
        marker_color = "gray"
        
        if is_rerouted:
            if node_name == route_decision.destination:
                # The target redirected node gets a beautiful red flashing/exclamation marker!
                marker_color = "red"
                popup_text += "<br><b style='color:#EF4444;'>📍 DIVERSION TARGET</b>"
            elif node_name in route_decision.path:
                marker_color = "orange"
            elif node_name == "regional_market":
                marker_color = "black"
                popup_text += "<br><b style='color:#6B7280;'>❌ BYPASSED</b>"
        else:
            if node_name == "regional_market":
                marker_color = "green"
            elif node_name in original_route_nodes:
                marker_color = "blue"
                
        # Draw current truck position marker
        if node_name == current_node:
            folium.Marker(
                location=coords,
                popup="🚚 <b>Current Truck Location</b>",
                tooltip="Current Position",
                icon=folium.Icon(color="orange", icon="truck", prefix="fa"),
            ).add_to(m)
            
            # Draw a decorative pulse circle around the truck
            folium.Circle(
                location=coords,
                radius=1000,
                color="#FBBF24",
                fill=True,
                fill_color="#FBBF24",
                fill_opacity=0.15,
            ).add_to(m)
        else:
            folium.Marker(
                location=coords,
                popup=popup_text,
                tooltip=node_style["name"],
                icon=folium.Icon(color=marker_color, icon=node_style["icon"], prefix="fa"),
            ).add_to(m)
            
    # Render map
    st_folium(m, height=480, use_container_width=True)

with main_right:
    # 2. Agent Decision & Logistics Analytics
    if is_rerouted:
        st.markdown("### 🤖 Agent Intervention Panel")
        
        # Compute dynamic spoilage hours remaining based on temperatures
        # If internal temp is high, it spoils faster
        hours_remaining = max(0.5, round((35.0 - payload_info["internal_temp"]) / 4.0, 1))
        
        # Fetch the decision from the LangChain-like Flash Intervention Agent
        agent_context = InterventionContext(
            cargo_type=payload_info["cargo_type"],
            cargo_description=f"5 tons of {payload_info['cargo_type']}",
            quantity_tons=5.0,
            hours_remaining=hours_remaining,
            risk_score=risk_score,
            route_path=route_decision.path,
            alternative_buyers=[
                BuyerSignal(buyer_id="buyer_fresh_mart", distance_km=6.8, local_demand_score=82.0, inventory_turnover_score=0.88),
                BuyerSignal(buyer_id="buyer_green_coop", distance_km=12.4, local_demand_score=75.0, inventory_turnover_score=0.79),
                BuyerSignal(buyer_id="buyer_urban_pop_up", distance_km=4.2, local_demand_score=91.0, inventory_turnover_score=0.82),
            ],
            base_unit_price=100.0,
        )
        
        agent_decision = flash_intervention_agent.decide(agent_context)
        
        # Render glowing card with selected buyer & discount
        st.markdown(
            f"""
            <div class="card card-critical">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1rem;">
                    <span style="font-size: 1.5rem;">⚠️</span>
                    <h4 style="margin: 0; color: #FCA5A5;">FLASH INTERVENTION DEPLOYED</h4>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <div class="card-title" style="margin-bottom:2px;">Target Buyer</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF;">
                            {agent_decision.selected_buyer_id.replace('_', ' ').title()}
                        </div>
                        <span style="font-size: 0.8rem; color: #6B7280; font-family: monospace;">ID: {agent_decision.selected_buyer_id}</span>
                    </div>
                    <div>
                        <div class="card-title" style="margin-bottom:2px;">Markdown Applied</div>
                        <div style="font-size: 1.7rem; font-weight: 800; color: #EF4444;">
                            -{agent_decision.markdown_percent}%
                        </div>
                    </div>
                </div>
                <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                    <div class="card-title">Intervention Rationale</div>
                    <p style="font-size: 0.9rem; line-height: 1.4; color: #D1D5DB; margin: 0;">
                        {agent_decision.rationale}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Render pricing adjustments table
        st.markdown("#### 💸 Modified Financial Breakdown")
        pricing_item = agent_decision.modified_pricing[0]
        pricing_df = pd.DataFrame([
            {"Metric": "SKU Item", "Value": str(pricing_item.sku)},
            {"Metric": "Quantity (Tons)", "Value": f"{pricing_item.quantity_tons:.1f} T"},
            {"Metric": "Original Unit Price", "Value": f"${pricing_item.original_unit_price:.2f}/ton"},
            {"Metric": "Discounted Unit Price", "Value": f"${pricing_item.discounted_unit_price:.2f}/ton"},
            {"Metric": "Original Value", "Value": f"${pricing_item.original_total_price:.2f}"},
            {"Metric": "Discounted Yield Value", "Value": f"${pricing_item.discounted_total_price:.2f}"},
            {"Metric": "Retained Revenue Loss Avoided", "Value": f"${pricing_item.discounted_total_price:.2f}"},
        ])
        st.table(pricing_df.set_index("Metric"))
        
        # Expandable notification webhooks
        with st.expander("🔗 Notification Webhook Envelope", expanded=False):
            st.markdown(
                f"""<pre class="json-code">{json.dumps(agent_decision.notification.model_dump(mode='json'), indent=2)}</pre>""",
                unsafe_allow_html=True,
            )
            
    else:
        st.markdown("### 📊 Logistics Analytics Panel")
        
        # Normal operations dashboard
        st.markdown(
            """
            <div class="card" style="border-left: 4px solid #10B981;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.3rem;">🟢</span>
                    <h5 style="margin: 0; color: #34D399; font-weight: 600;">FLEET OPERATIONS SECURE</h5>
                </div>
                <p style="font-size: 0.9rem; color: #9CA3AF; margin: 0;">
                    Telemetry is stable. Cargo temperature is within safe threshold limits. The autonomous agent remains in monitoring mode.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Draw graph of historical temperatures if data exists
        if len(st.session_state.telemetry_history) > 0:
            hist_df = pd.DataFrame(st.session_state.telemetry_history)
            hist_df["tick"] = range(1, len(hist_df) + 1)
            
            st.markdown("#### 🌡️ Temperature Trends (°C)")
            st.line_chart(hist_df.set_index("tick")[["internal_temp", "ambient_temp"]])
            
            st.markdown("#### 📈 Cumulative Spoilage Risk Curve")
            st.area_chart(hist_df.set_index("tick")["risk_score"])
        else:
            st.caption("Awaiting telemetry reports to render analytics trends.")

# Historical Telemetry Log Table
st.markdown("---")
st.markdown("### 📋 Historical Telemetry Log")

if len(st.session_state.telemetry_history) > 0:
    log_df = pd.DataFrame(st.session_state.telemetry_history)
    log_df["timestamp"] = log_df["timestamp"].apply(lambda t: t.strftime("%Y-%m-%d %H:%M:%S UTC"))
    log_df["risk_score"] = log_df["risk_score"].apply(lambda r: f"{r*100:.2f}%")
    log_df["internal_temp"] = log_df["internal_temp"].apply(lambda t: f"{t:.1f}°C")
    log_df["ambient_temp"] = log_df["ambient_temp"].apply(lambda t: f"{t:.1f}°C")
    st.dataframe(
        log_df[["timestamp", "internal_temp", "ambient_temp", "risk_score", "state"]].iloc[::-1],
        use_container_width=True,
    )
else:
    st.info("Log is empty. Inject telemetry to see records.")
