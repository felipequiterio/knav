from dotenv import load_dotenv
import streamlit as st
import krpc
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

load_dotenv()

# Connect to KSP
try:
    conn = krpc.connect(
        name="Telemetry Connection",
        address=os.getenv("IP"),
        rpc_port=8077,
        stream_port=8078,
    )
    space_center = conn.space_center
    vessel = space_center.active_vessel
    nrf = vessel.orbit.body.non_rotating_reference_frame  # Planet-centred inertial-ish
    flt = vessel.flight(nrf)
    connection_status = "Connected"
except Exception as e:
    st.error(f"Failed to connect to KSP: {e}")
    st.stop()

st.set_page_config(
    page_title="KSP Autonomous Navigation Dashboard",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 KSP Autonomous Navigation Dashboard")
st.markdown("---")

# Initialize session state for data storage
if "telemetry_data" not in st.session_state:
    st.session_state.telemetry_data = []

# Sidebar controls
st.sidebar.title("Dashboard Controls")
update_frequency = st.sidebar.slider("Update Frequency (seconds)", 0.1, 5.0, 1.0, 0.1)
max_data_points = st.sidebar.slider("Max Data Points", 50, 500, 100)
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)

# Time information in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### ⏰ Time Information")
if "telemetry_data" in st.session_state and st.session_state.telemetry_data:
    latest_data = st.session_state.telemetry_data[-1]
    latest_ut = latest_data["time"]
    latest_warp = latest_data["warp_rate"]

    def format_ut_time_sidebar(ut_seconds):
        days = int(ut_seconds // 86400)
        hours = int((ut_seconds % 86400) // 3600)
        minutes = int((ut_seconds % 3600) // 60)
        seconds = int(ut_seconds % 60)
        return f"Day {days}, {hours:02d}:{minutes:02d}:{seconds:02d}"

    st.sidebar.info(f"**Current UT:** {format_ut_time_sidebar(latest_ut)}")
    warp_color = "🔴" if latest_warp > 1000 else "🟡" if latest_warp > 10 else "🟢"
    st.sidebar.info(f"**Time Warp:** {warp_color} {latest_warp:.0f}x")

# Manual refresh button
if st.sidebar.button("Manual Refresh") or auto_refresh:
    # Create placeholder for dynamic content
    placeholder = st.empty()

    # Continuous data collection loop
    for iteration in range(1000):  # Run for a long time
        try:
            # Get current telemetry data
            current_ut = space_center.ut  # Universal Time in seconds
            warp_rate = space_center.warp_rate  # Current time warp rate
            warp_factor = space_center.warp_factor  # Current warp factor

            # Convert UT to readable format (days, hours, minutes, seconds)
            def format_ut_time(ut_seconds):
                days = int(ut_seconds // 86400)  # 86400 seconds per day
                hours = int((ut_seconds % 86400) // 3600)  # 3600 seconds per hour
                minutes = int((ut_seconds % 3600) // 60)
                seconds = int(ut_seconds % 60)
                return f"Day {days}, {hours:02d}:{minutes:02d}:{seconds:02d}"

            # Basic vessel info
            vessel_name = vessel.name
            body_name = vessel.orbit.body.name

            # Flight data
            altitude = flt.mean_altitude
            surface_altitude = flt.surface_altitude
            velocity = flt.speed
            vertical_speed = flt.vertical_speed

            # Orbital data
            apoapsis = vessel.orbit.apoapsis_altitude
            periapsis = vessel.orbit.periapsis_altitude
            orbital_speed = vessel.orbit.speed

            # Resources (fuel)
            total_fuel = 0
            total_fuel_capacity = 0
            for resource in vessel.resources.all:
                if resource.name == "LiquidFuel":
                    total_fuel += resource.amount
                    total_fuel_capacity += resource.max

            fuel_percentage = (
                (total_fuel / total_fuel_capacity * 100)
                if total_fuel_capacity > 0
                else 0
            )

            # Engine status
            engines = vessel.parts.engines
            active_engines = sum(1 for engine in engines if engine.active)
            total_engines = len(engines)

            # Store data
            telemetry_point = {
                "time": current_ut,
                "warp_rate": warp_rate,
                "altitude": altitude,
                "surface_altitude": surface_altitude,
                "velocity": velocity,
                "vertical_speed": vertical_speed,
                "apoapsis": apoapsis,
                "periapsis": periapsis,
                "orbital_speed": orbital_speed,
                "fuel_percentage": fuel_percentage,
                "active_engines": active_engines,
            }

            # Add to session state
            st.session_state.telemetry_data.append(telemetry_point)

            # Keep only last N data points
            if len(st.session_state.telemetry_data) > max_data_points:
                st.session_state.telemetry_data = st.session_state.telemetry_data[
                    -max_data_points:
                ]

            # Convert to DataFrame for plotting
            df = pd.DataFrame(st.session_state.telemetry_data)

            with placeholder.container():
                # Connection status
                time_warp_info = (
                    f" | ⏱️ Time Warp: {warp_rate:.0f}x" if warp_rate > 1 else ""
                )
                st.success(
                    f"🔗 Connected to KSP | Vessel: {vessel_name} | Body: {body_name}{time_warp_info}"
                )

                # Create KPI columns
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric(
                        label="🏔️ Altitude",
                        value=f"{altitude:,.0f} m",
                        delta=f"{vertical_speed:+.1f} m/s",
                    )

                with col2:
                    st.metric(
                        label="🚀 Velocity",
                        value=f"{velocity:,.0f} m/s",
                        delta=f"{velocity - (df['velocity'].iloc[-2] if len(df) > 1 else velocity):+.1f}",
                    )

                with col3:
                    st.metric(
                        label="⛽ Fuel",
                        value=f"{fuel_percentage:.1f}%",
                        delta=f"{fuel_percentage - (df['fuel_percentage'].iloc[-2] if len(df) > 1 else fuel_percentage):+.1f}%",
                    )

                with col4:
                    st.metric(
                        label="🔥 Engines",
                        value=f"{active_engines}/{total_engines}",
                        delta=f"{active_engines - (df['active_engines'].iloc[-2] if len(df) > 1 else active_engines):+.0f}",
                    )

                with col5:
                    st.metric(
                        label="🛰️ Orbital Speed",
                        value=f"{orbital_speed:,.0f} m/s",
                        delta=f"{orbital_speed - (df['orbital_speed'].iloc[-2] if len(df) > 1 else orbital_speed):+.1f}",
                    )

                st.markdown("---")

                # Charts
                if len(df) > 1:
                    # Create two columns for charts
                    chart_col1, chart_col2 = st.columns(2)

                    with chart_col1:
                        st.markdown("### 📈 Altitude & Velocity Over Time")

                        # Convert UT time to relative time for better readability
                        df_chart = df.copy()
                        df_chart["relative_time"] = (
                            df_chart["time"] - df_chart["time"].iloc[0]
                        )

                        # Show mission elapsed time
                        mission_elapsed = current_ut - df_chart["time"].iloc[0]
                        if mission_elapsed > 3600:  # More than 1 hour
                            elapsed_str = f"{mission_elapsed / 3600:.1f} hours"
                        elif mission_elapsed > 60:  # More than 1 minute
                            elapsed_str = f"{mission_elapsed / 60:.1f} minutes"
                        else:
                            elapsed_str = f"{mission_elapsed:.1f} seconds"

                        st.caption(f"📊 Mission elapsed time: {elapsed_str}")

                        # Create dual-axis plot
                        fig = go.Figure()

                        fig.add_trace(
                            go.Scatter(
                                x=df_chart["relative_time"],
                                y=df_chart["altitude"],
                                mode="lines",
                                name="Altitude (m)",
                                line=dict(color="blue"),
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=df_chart["relative_time"],
                                y=df_chart["velocity"],
                                mode="lines",
                                name="Velocity (m/s)",
                                yaxis="y2",
                                line=dict(color="red"),
                            )
                        )

                        fig.update_layout(
                            xaxis=dict(title="Time (seconds since start)"),
                            yaxis=dict(title="Altitude (m)", side="left"),
                            yaxis2=dict(
                                title="Velocity (m/s)", side="right", overlaying="y"
                            ),
                            height=400,
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    with chart_col2:
                        st.markdown("### 🛰️ Orbital Parameters")

                        fig2 = go.Figure()

                        fig2.add_trace(
                            go.Scatter(
                                x=df_chart["relative_time"],
                                y=df_chart["apoapsis"],
                                mode="lines",
                                name="Apoapsis",
                                line=dict(color="orange"),
                            )
                        )

                        fig2.add_trace(
                            go.Scatter(
                                x=df_chart["relative_time"],
                                y=df_chart["periapsis"],
                                mode="lines",
                                name="Periapsis",
                                line=dict(color="purple"),
                            )
                        )

                        fig2.update_layout(
                            xaxis=dict(title="Time (seconds since start)"),
                            yaxis=dict(title="Altitude (m)"),
                            height=400,
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                    # Full-width fuel chart
                    st.markdown("### ⛽ Fuel Level Over Time")
                    fig3 = px.line(
                        df_chart,
                        x="relative_time",
                        y="fuel_percentage",
                        title="Fuel Percentage",
                        labels={
                            "fuel_percentage": "Fuel (%)",
                            "relative_time": "Time (seconds since start)",
                        },
                    )
                    fig3.update_traces(line_color="green")
                    st.plotly_chart(fig3, use_container_width=True)

                # Raw telemetry data table
                st.markdown("### 📊 Current Telemetry Data")

                col_data1, col_data2 = st.columns(2)

                with col_data1:
                    st.json(
                        {
                            "Vessel Name": vessel_name,
                            "Body": body_name,
                            "Universal Time": format_ut_time(current_ut),
                            "Time Warp": f"{warp_rate:.0f}x"
                            if warp_rate > 1
                            else "1x (Normal)",
                            "Mean Altitude": f"{altitude:,.2f} m",
                            "Surface Altitude": f"{surface_altitude:,.2f} m",
                            "Velocity": f"{velocity:,.2f} m/s",
                            "Vertical Speed": f"{vertical_speed:+.2f} m/s",
                        }
                    )

                with col_data2:
                    st.json(
                        {
                            "Apoapsis": f"{apoapsis:,.2f} m",
                            "Periapsis": f"{periapsis:,.2f} m",
                            "Orbital Speed": f"{orbital_speed:,.2f} m/s",
                            "Fuel Level": f"{fuel_percentage:.1f}%",
                            "Active Engines": f"{active_engines}/{total_engines}",
                        }
                    )

                # Historical data table
                if len(df) > 0:
                    st.markdown("### 📋 Historical Data")
                    # Show last 10 records
                    display_df = df.tail(10).copy()
                    # Convert UT to readable format
                    display_df["UT_Time"] = display_df["time"].apply(format_ut_time)
                    display_df["Warp"] = display_df["warp_rate"].apply(
                        lambda x: f"{x:.0f}x" if x > 1 else "1x"
                    )
                    display_df = display_df.drop(["time", "warp_rate"], axis=1)
                    # Reorder columns to put time info first
                    cols = ["UT_Time", "Warp"] + [
                        col
                        for col in display_df.columns
                        if col not in ["UT_Time", "Warp"]
                    ]
                    display_df = display_df[cols]
                    st.dataframe(display_df, use_container_width=True)

        except Exception as e:
            st.error(f"Error reading telemetry: {e}")
            break

        # Adaptive update frequency based on time warp
        # During high time warp, update more frequently to capture more data
        adaptive_frequency = update_frequency
        if warp_rate > 1:
            # Reduce sleep time proportionally to warp rate, but cap it
            adaptive_frequency = max(0.1, update_frequency / min(warp_rate, 10))

        # Wait before next update
        time.sleep(adaptive_frequency)

        # Break if auto refresh is disabled
        if not auto_refresh:
            break

else:
    st.info(
        "Click 'Manual Refresh' or enable 'Auto Refresh' to start collecting telemetry data."
    )
