import krpc
import os
import sys
from pathlib import Path

# Add the parent directory (project root) to Python path to access core modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import streamlit as st
from components.sidebar import create_sidebar
from core.launch.gravity_turn import pre_launch, gravity_turn
from core.orbital.circularization import circularization
from core.utils.helpers import execute_node
from core.orbital.ht import hohmann_transfer

load_dotenv()


# Connect to KSP
@st.cache_resource
def connect_to_ksp():
    try:
        conn = krpc.connect(
            name="Mission Control",
            address=os.getenv("IP"),
            rpc_port=8077,
            stream_port=8078,
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to KSP: {e}")
        return None


conn = connect_to_ksp()
if conn is None:
    st.stop()

st.set_page_config(
    page_title="Mission Control",
    page_icon="📟",
    layout="wide",
)
st = create_sidebar(st)

space_center = conn.space_center
vessel = space_center.active_vessel
nrf = vessel.orbit.body.non_rotating_reference_frame  # Planet-centred inertial-ish
flt = vessel.flight(nrf)

vessel_name = conn.space_center.active_vessel.name

# Example: "D25-L-01-[DL-MUN-03]"
# Rocket: everything before the first '[' (strip trailing '-')
if "[" in vessel_name and "]" in vessel_name:
    rocket_name = vessel_name.split("[")[0].rstrip("-").strip()
    payload_name = vessel_name.split("[")[1].split("]")[0].strip()
else:
    rocket_name = vessel_name
    payload_name = ""

st.title(f"🚀 {rocket_name} | 🛰️ {payload_name}")
st.markdown("---")

# Get body parameters for realistic orbit input range
body = vessel.orbit.body
atmosphere_height = body.atmosphere_depth if body.has_atmosphere else 0
soi_radius = body.sphere_of_influence

# Convert to kilometers for better display
atmosphere_height_km = atmosphere_height / 1000
soi_radius_km = soi_radius / 1000

# Set default orbit to a reasonable altitude above atmosphere
default_orbit_km = atmosphere_height_km + 100 if body.has_atmosphere else 100

# pre_launch()
# gravity_turn()
# circularization()
orbit_input = st.number_input(
    f"Target Orbit Altitude (km) - {body.name}",
    value=default_orbit_km,
    min_value=atmosphere_height_km,
    max_value=soi_radius_km,
    step=10.0,
    format="%.1f",
)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    if st.button("Execute Launch Sequence"):
        pre_launch()
        gravity_turn()
        circularization()

with col2:
    if st.button("Execute Pre-launch checks"):
        pre_launch()

with col3:
    if st.button("Execute Gravity turn"):
        gravity_turn()


with col4:
    if st.button("Execute Circularization"):
        circularization()

with col5:
    if st.button("Create Hohmann Transfer Node"):
        hohmann_transfer("Mun")

with col6:
    if st.button("Execute Maneuver Node"):
        execute_node()
st.markdown("---")
