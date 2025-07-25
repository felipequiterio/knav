import streamlit as st
import sys
import os
import time
from collections import deque

# Add the project root to Python path to find the utils module
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils import SpaceLogger

def initialize_session_state():
    """Initialize session state variables for logging."""
    if 'mission_logs' not in st.session_state:
        st.session_state.mission_logs = deque(maxlen=200)
    if 'logger_initialized' not in st.session_state:
        st.session_state.logger_initialized = False

class StreamlitLogger:
    """Simplified logger that stores messages directly in session state."""
    
    def __init__(self, name: str):
        self.name = name
        
    def _add_log(self, level, emoji, tag, message):
        """Add a log entry to session state."""
        initialize_session_state()
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {emoji} [{tag}] {message}"
        st.session_state.mission_logs.append(log_entry)
    
    def status(self, message):
        self._add_log("INFO", "📊", "STAT", message)
    
    def info(self, message):
        self._add_log("INFO", "🟢", "INFO", message)
    
    def warning(self, message):
        self._add_log("WARN", "⚠️", "WARN", message)
    
    def error(self, message):
        self._add_log("ERROR", "❌", "ERR ", message)
    
    def burn(self, message):
        self._add_log("INFO", "🔥", "BURN", message)
    
    def maneuver(self, message):
        self._add_log("INFO", "🛰️", "MNVR", message)
    
    def align(self, message):
        self._add_log("INFO", "🎯", "ALGN", message)
    
    def warp(self, message):
        self._add_log("INFO", "⏩", "WARP", message)
    
    def sas(self, message):
        self._add_log("INFO", "🧭", "SAS ", message)
    
    def auto_pilot(self, message):
        self._add_log("INFO", "🤖", "APLT", message)
    
    def mission_start(self, name):
        self._add_log("INFO", "🚀", "STRT", f"Mission {name} initiated")
    
    def mission_complete(self, name):
        self._add_log("INFO", "✅", "COMP", f"Mission {name} completed successfully")

def get_mission_logger():
    """Get or create the mission control logger instance."""
    initialize_session_state()
    
    if not st.session_state.logger_initialized:
        st.session_state.logger_initialized = True
        # Add some initial logs to show it's working
        logger = StreamlitLogger("Mission_Control")
        logger.status("Logger system initialized")
        return logger
    return StreamlitLogger("Mission_Control")

def create_logger_mission_control(st_module):
    """
    Create a logger display section for mission control interface.
    
    Args:
        st_module: Streamlit module instance
    """
    initialize_session_state()
    st_module.markdown("### 📋 Mission Logs")
    
    # Controls in expander
    with st_module.expander("Logger Controls", expanded=False):
        col_a, col_b, col_c = st_module.columns(3)
        with col_a:
            max_log_entries = st_module.slider("Max Entries", 10, 100, 50, key="log_max")
        with col_b:
            auto_refresh = st_module.checkbox("Auto Refresh", value=True, key="log_refresh")
        with col_c:
            if st_module.button("Clear Logs", key="log_clear"):
                st.session_state.mission_logs.clear()
                st_module.success("Logs cleared!")
    
    # Display logs
    current_logs = list(st.session_state.mission_logs)
    
    if current_logs:
        # Limit to max entries
        display_logs = current_logs[-max_log_entries:] if len(current_logs) > max_log_entries else current_logs
        
        # Create log display
        log_text = "\n".join(display_logs)
        st_module.code(log_text, language=None, line_numbers=False)
        
        # Statistics
        col1, col2, col3 = st_module.columns(3)
        with col1:
            st_module.metric("Total Logs", len(current_logs))
        with col2:
            st_module.metric("Displayed", len(display_logs))
        with col3:
            if current_logs:
                latest_time = current_logs[-1].split(']')[0].replace('[', '')
                st_module.metric("Latest", latest_time)
    else:
        st_module.info("🤖 No mission logs yet. Start a mission to see logs here.")
        
        # Add test button
        if st_module.button("Add Test Log", key="test_log"):
            logger = StreamlitLogger("Test")
            logger.status("Test log entry added")
            logger.burn("Engine ignition test")
            logger.maneuver("Test maneuver logged")
            st_module.rerun()
    
    # Auto refresh
    if auto_refresh and current_logs:
        time.sleep(0.5)
        st_module.rerun() 