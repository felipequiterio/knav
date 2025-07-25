import pandas as pd
import sys
import os
import time
import math

# Add the project root to Python path to find the core module
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from core.utils.formulas import acceleration


def create_telemetry_mission_control(st, space_center, vessel, nrf, flt):
    # Manual refresh button
    # Create placeholder for dynamic content
    st.sidebar.title("Dashboard Controls")
    update_frequency = st.sidebar.slider(
        "Update Frequency (seconds)", 0.1, 5.0, 1.0, 0.1
    )
    max_data_points = st.sidebar.slider("Max Data Points", 50, 500, 100)
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)

    # Initialize session state for data storage
    if "telemetry_data" not in st.session_state:
        st.session_state.telemetry_data = []

    placeholder = st.empty()

    # Continuous data collection loop
    while True:  # Run for a long time
        try:
            # Get current telemetry data
            current_ut = space_center.ut  # Universal Time in seconds
            warp_rate = space_center.warp_rate  # Current time warp rate

            # Convert UT to readable format (days, hours, minutes, seconds) for KSP (1 day = 6 hours)
            def format_ut_time(ut_seconds):
                KSP_DAY_SECONDS = 6 * 3600  # 21600 seconds per KSP day
                days = int(ut_seconds // KSP_DAY_SECONDS)
                hours = int((ut_seconds % KSP_DAY_SECONDS) // 3600)
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

            # Telemetry data
            thrust = vessel.available_thrust
            mass = vessel.mass
            vessel_acceleration = acceleration(thrust, mass)

            # Orbital data
            apoapsis = vessel.orbit.apoapsis_altitude
            periapsis = vessel.orbit.periapsis_altitude
            orbital_speed = vessel.orbit.speed
            time_to_apoapsis = vessel.orbit.time_to_apoapsis
            time_to_periapsis = vessel.orbit.time_to_periapsis
            orbital_period = vessel.orbit.period
            eccentricity = vessel.orbit.eccentricity
            inclination = vessel.orbit.inclination * (180 / math.pi)  # Convert radians to degrees
            current_radius = vessel.orbit.radius

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

            # Calculate battery percentage for data tracking
            battery_amount = 0
            battery_capacity = 0
            for resource in vessel.resources.all:
                if resource.name == "ElectricCharge":
                    battery_amount += resource.amount
                    battery_capacity += resource.max

            battery_percentage = (
                (battery_amount / battery_capacity * 100)
                if battery_capacity > 0
                else 0
            )

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
                "time_to_apoapsis": time_to_apoapsis,
                "time_to_periapsis": time_to_periapsis,
                "orbital_period": orbital_period,
                "eccentricity": eccentricity,
                "inclination": inclination,
                "current_radius": current_radius,
                "fuel_percentage": fuel_percentage,
                "battery_percentage": battery_percentage,
                "active_engines": active_engines,
                "acceleration": vessel_acceleration,
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
                st.markdown("### 🎚️ Flight Data")
                # Create KPI columns
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric(
                        label="🏔️ Surface Altitude",
                        value=f"{surface_altitude:,.0f} m",
                        delta=f"{surface_altitude - (df['surface_altitude'].iloc[-2] if len(df) > 1 else surface_altitude):+.1f}",
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
                        label="💨 Acceleration",
                        value=f"{vessel_acceleration:,.0f} m/s²",
                        delta=f"{vessel_acceleration - (df['acceleration'].iloc[-2] if len(df) > 1 else vessel_acceleration):+.1f}",
                    )

                

                st.markdown("---")
                st.markdown("### 🛰️ Orbital Data")

                # Helper function to format time
                def format_time(seconds):
                    if seconds < 0:
                        return "N/A"
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    if hours > 0:
                        return f"{hours}h {minutes}m {secs}s"
                    elif minutes > 0:
                        return f"{minutes}m {secs}s"
                    else:
                        return f"{secs}s"
                    
                col6, col7, col8, col9 = st.columns(4)

                with col6:
                    st.metric(
                        label="🔼 Apoapsis",
                        value=f"{apoapsis:,.0f} m",
                        delta=f"{apoapsis - (df['apoapsis'].iloc[-2] if len(df) > 1 else apoapsis):+.1f}",
                    )

                with col7:
                    st.metric(
                        label="⏱️ Time to Ap",
                        value=format_time(time_to_apoapsis),
                        delta=f"{time_to_apoapsis - (df['time_to_apoapsis'].iloc[-2] if len(df) > 1 else time_to_apoapsis):+.1f}s"
                    )

                with col8:
                    st.metric(
                        label="🔽 Periapsis",
                        value=f"{periapsis:,.0f} m",
                        delta=f"{periapsis - (df['periapsis'].iloc[-2] if len(df) > 1 else periapsis):+.1f}",
                    )
                
                with col9:
                    st.metric(
                        label="⏱️ Time to Pe",
                        value=format_time(time_to_periapsis),
                        delta=f"{time_to_periapsis - (df['time_to_periapsis'].iloc[-2] if len(df) > 1 else time_to_periapsis):+.1f}s"
                    )

                st.markdown("---")
                st.markdown("### 🚀 Vessel Data")
                col16, col17, col18, col19, col20 = st.columns(5)

                # Get communication status
                comms = vessel.comms
                can_communicate = comms.can_communicate
                signal_strength = comms.signal_strength
                
                # Get current battery percentage from telemetry data
                current_battery_percentage = df['battery_percentage'].iloc[-1] if len(df) > 0 else 0

                with col16:
                    st.metric(
                        label="⛽ Fuel",
                        value=f"{fuel_percentage:.1f}%",
                        delta=f"{fuel_percentage - (df['fuel_percentage'].iloc[-2] if len(df) > 1 else fuel_percentage):+.1f}%",
                    )

                with col17:
                    st.metric(
                        label="🔋 Battery",
                        value=f"{current_battery_percentage:.1f}%",
                        delta=f"{current_battery_percentage - (df['battery_percentage'].iloc[-2] if len(df) > 1 else current_battery_percentage):+.1f}%",
                    )

                with col18:
                    connection_status = "🟢 Connected" if can_communicate else "🔴 No Signal"
                    signal_strength_percent = signal_strength * 100
                    st.metric(
                        label="📡 Connection",
                        value=f"{signal_strength_percent:.1f}%",
                        delta=connection_status
                    )

                with col19:
                    st.metric(
                        label="🚀 Engines",
                        value=f"{active_engines}/{total_engines}",
                        delta=f"Active: {active_engines}"
                    )

                with col20:
                    st.metric(
                        label="💨 Thrust",
                        value=f"{thrust:,.0f} N",
                        delta=f"Available: {vessel.available_thrust:,.0f} N"
                    )
                
        except Exception as e:
            st.error(f"Error reading telemetry: {e}")
            break

        # Respect the update frequency and auto refresh settings
        if auto_refresh:
            time.sleep(update_frequency)
        else:
            break
