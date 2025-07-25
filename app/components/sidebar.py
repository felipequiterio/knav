def create_sidebar(st):
    st.sidebar.title("Dashboard Pages")

    st.sidebar.page_link(page="mission_control.py", label="Mission Control", icon="📟")
    st.sidebar.page_link(page="pages/home.py", label="Home", icon="🏠")
    st.sidebar.page_link(page="pages/telemetry.py", label="Telemetry", icon="🔍")
    st.sidebar.page_link(page="pages/settings.py", label="Settings", icon="⚙️")
    st.sidebar.page_link(page="pages/navigation.py", label="Navigation", icon="🧭")

    st.sidebar.markdown("---")

    return st
