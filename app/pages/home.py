from dotenv import load_dotenv
import streamlit as st
import krpc
import os
import time
import numpy as np
import plotly.graph_objects as go
import math

load_dotenv()


# Connect to KSP
@st.cache_resource
def connect_to_ksp():
    try:
        conn = krpc.connect(
            name="3D Orbital Viewer",
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

space_center = conn.space_center
vessel = space_center.active_vessel

st.set_page_config(
    page_title="KSP 3D Orbital Viewer",
    page_icon="🛰️",
    layout="wide",
)

st.title("🛰️ KSP 3D Orbital Viewer")
st.markdown("---")

# Initialize session state for orbital data storage
if "orbital_positions" not in st.session_state:
    st.session_state.orbital_positions = []
if "predicted_orbit" not in st.session_state:
    st.session_state.predicted_orbit = []

# Sidebar controls
st.sidebar.title("3D Orbital Controls")
update_frequency = st.sidebar.slider("Update Frequency (seconds)", 0.1, 2.0, 0.5, 0.1)
max_trail_points = st.sidebar.slider("Orbital Trail Points", 50, 500, 200)
show_predicted_orbit = st.sidebar.checkbox("Show Predicted Orbit", value=True)
show_orbital_trail = st.sidebar.checkbox("Show Orbital Trail", value=True)
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)

# Reference frame selection
reference_frame_option = st.sidebar.selectbox(
    "Reference Frame",
    ["Body-Fixed", "Inertial"],
    index=1,
    help="Body-Fixed rotates with the planet, Inertial is space-fixed",
)

# Manual refresh button
if st.sidebar.button("Manual Refresh") or auto_refresh:
    placeholder = st.empty()

    # Get reference frames
    if reference_frame_option == "Body-Fixed":
        ref_frame = vessel.orbit.body.reference_frame
    else:
        ref_frame = vessel.orbit.body.non_rotating_reference_frame

    # Continuous data collection loop
    for iteration in range(1000):
        try:
            # Get vessel information
            vessel_name = vessel.name
            body = vessel.orbit.body
            body_name = body.name
            body_radius = body.equatorial_radius

            # Get vessel position in the selected reference frame
            position = vessel.position(ref_frame)
            velocity = vessel.velocity(ref_frame)

            # Convert position to kilometers for better visualization
            pos_x, pos_y, pos_z = [p / 1000 for p in position]  # Convert to km
            vel_x, vel_y, vel_z = velocity

            # Get orbital parameters
            orbit = vessel.orbit
            apoapsis = orbit.apoapsis_altitude
            periapsis = orbit.periapsis_altitude
            inclination = math.degrees(orbit.inclination)
            eccentricity = orbit.eccentricity
            orbital_period = orbit.period
            mean_anomaly = orbit.mean_anomaly_at_epoch

            # Store current position
            current_time = space_center.ut
            position_data = {
                "time": current_time,
                "x": pos_x,
                "y": pos_y,
                "z": pos_z,
                "velocity_magnitude": math.sqrt(vel_x**2 + vel_y**2 + vel_z**2),
            }

            # Add to orbital positions
            st.session_state.orbital_positions.append(position_data)

            # Keep only last N points for trail
            if len(st.session_state.orbital_positions) > max_trail_points:
                st.session_state.orbital_positions = st.session_state.orbital_positions[
                    -max_trail_points:
                ]

            # Calculate predicted orbital path if requested
            predicted_positions = []
            if show_predicted_orbit and len(st.session_state.orbital_positions) > 10:
                try:
                    # Generate points along the predicted orbit
                    num_points = 100
                    current_mean_anomaly = orbit.mean_anomaly_at_epoch

                    for i in range(num_points):
                        # Calculate mean anomaly for this point
                        anomaly_step = (2 * math.pi * i) / num_points
                        future_time = (
                            current_time
                            + (anomaly_step / (2 * math.pi)) * orbital_period
                        )

                        try:
                            # Get position at future time
                            future_pos = orbit.position_at(future_time, ref_frame)
                            pred_x, pred_y, pred_z = [p / 1000 for p in future_pos]
                            predicted_positions.append([pred_x, pred_y, pred_z])
                        except:
                            # Skip if we can't calculate this point
                            continue

                    st.session_state.predicted_orbit = predicted_positions
                except Exception:
                    # If prediction fails, use empty list
                    st.session_state.predicted_orbit = []

            with placeholder.container():
                # Status information
                st.success(
                    f"🔗 Connected | Vessel: {vessel_name} | Orbiting: {body_name}"
                )

                # Create info columns
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("🏔️ Apoapsis", f"{apoapsis / 1000:.1f} km")
                    st.metric("🕳️ Periapsis", f"{periapsis / 1000:.1f} km")

                with col2:
                    st.metric("📐 Inclination", f"{inclination:.1f}°")
                    st.metric("📊 Eccentricity", f"{eccentricity:.3f}")

                with col3:
                    st.metric("⏱️ Orbital Period", f"{orbital_period / 60:.1f} min")
                    st.metric(
                        "🚀 Velocity", f"{position_data['velocity_magnitude']:.0f} m/s"
                    )

                with col4:
                    alt_current = math.sqrt(pos_x**2 + pos_y**2 + pos_z**2) - (
                        body_radius / 1000
                    )
                    st.metric("📍 Current Altitude", f"{alt_current:.1f} km")
                    st.metric("🌍 Body Radius", f"{body_radius / 1000:.1f} km")

                st.markdown("---")

                # Create 3D orbital plot
                st.markdown("### 🛰️ 3D Orbital View")

                fig = go.Figure()

                # Add the celestial body (sphere)
                body_radius_km = body_radius / 1000
                u, v = np.mgrid[0 : 2 * np.pi : 20j, 0 : np.pi : 10j]
                x_sphere = body_radius_km * np.cos(u) * np.sin(v)
                y_sphere = body_radius_km * np.sin(u) * np.sin(v)
                z_sphere = body_radius_km * np.cos(v)

                fig.add_trace(
                    go.Surface(
                        x=x_sphere,
                        y=y_sphere,
                        z=z_sphere,
                        name=body_name,
                        colorscale="Earth",
                        showscale=False,
                        opacity=0.8,
                    )
                )

                # Add orbital trail if enabled
                if show_orbital_trail and len(st.session_state.orbital_positions) > 1:
                    trail_x = [pos["x"] for pos in st.session_state.orbital_positions]
                    trail_y = [pos["y"] for pos in st.session_state.orbital_positions]
                    trail_z = [pos["z"] for pos in st.session_state.orbital_positions]

                    fig.add_trace(
                        go.Scatter3d(
                            x=trail_x,
                            y=trail_y,
                            z=trail_z,
                            mode="lines",
                            name="Orbital Trail",
                            line=dict(color="cyan", width=3),
                            opacity=0.7,
                        )
                    )

                # Add predicted orbit if enabled
                if show_predicted_orbit and st.session_state.predicted_orbit:
                    pred_x = [pos[0] for pos in st.session_state.predicted_orbit]
                    pred_y = [pos[1] for pos in st.session_state.predicted_orbit]
                    pred_z = [pos[2] for pos in st.session_state.predicted_orbit]

                    fig.add_trace(
                        go.Scatter3d(
                            x=pred_x,
                            y=pred_y,
                            z=pred_z,
                            mode="lines",
                            name="Predicted Orbit",
                            line=dict(color="yellow", width=2, dash="dash"),
                            opacity=0.5,
                        )
                    )

                # Add current vessel position
                fig.add_trace(
                    go.Scatter3d(
                        x=[pos_x],
                        y=[pos_y],
                        z=[pos_z],
                        mode="markers",
                        name="Current Position",
                        marker=dict(color="red", size=8, symbol="diamond"),
                    )
                )

                # Add velocity vector (scaled for visibility)
                scale_factor = 50  # Scale velocity vector for visibility
                vel_end_x = pos_x + (vel_x / 1000) * scale_factor
                vel_end_y = pos_y + (vel_y / 1000) * scale_factor
                vel_end_z = pos_z + (vel_z / 1000) * scale_factor

                fig.add_trace(
                    go.Scatter3d(
                        x=[pos_x, vel_end_x],
                        y=[pos_y, vel_end_y],
                        z=[pos_z, vel_end_z],
                        mode="lines",
                        name="Velocity Vector",
                        line=dict(color="orange", width=4),
                        opacity=0.8,
                    )
                )

                # Update layout for better 3D visualization
                max_range = (
                    max(body_radius_km * 3, abs(pos_x), abs(pos_y), abs(pos_z)) * 1.2
                )

                fig.update_layout(
                    scene=dict(
                        xaxis=dict(title="X (km)", range=[-max_range, max_range]),
                        yaxis=dict(title="Y (km)", range=[-max_range, max_range]),
                        zaxis=dict(title="Z (km)", range=[-max_range, max_range]),
                        aspectmode="cube",
                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
                    ),
                    title=f"3D Orbital View - {vessel_name} around {body_name}",
                    height=600,
                    showlegend=True,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Additional orbital information
                col_info1, col_info2 = st.columns(2)

                with col_info1:
                    st.markdown("### 📊 Current Position")
                    st.json(
                        {
                            "X Position": f"{pos_x:.2f} km",
                            "Y Position": f"{pos_y:.2f} km",
                            "Z Position": f"{pos_z:.2f} km",
                            "Distance from Center": f"{math.sqrt(pos_x**2 + pos_y**2 + pos_z**2):.2f} km",
                            "Reference Frame": reference_frame_option,
                        }
                    )

                with col_info2:
                    st.markdown("### 🚀 Velocity Vector")
                    st.json(
                        {
                            "X Velocity": f"{vel_x:.2f} m/s",
                            "Y Velocity": f"{vel_y:.2f} m/s",
                            "Z Velocity": f"{vel_z:.2f} m/s",
                            "Total Velocity": f"{math.sqrt(vel_x**2 + vel_y**2 + vel_z**2):.2f} m/s",
                            "Trail Points": len(st.session_state.orbital_positions),
                        }
                    )

        except Exception as e:
            st.error(f"Error collecting orbital data: {e}")
            break

        # Wait before next update
        time.sleep(update_frequency)

        # Break if auto refresh is disabled
        if not auto_refresh:
            break

else:
    st.info(
        "Click 'Manual Refresh' or enable 'Auto Refresh' to start the 3D orbital viewer."
    )
