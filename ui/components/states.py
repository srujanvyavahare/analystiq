import streamlit as st

def render_empty_state(icon: str, title: str, description: str):
    """
    Renders a centered empty state for inactive tabs.
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 50px 20px; color: #64748B;">
        <div style="font-size: 48px; margin-bottom: 20px;">{icon}</div>
        <h3 style="color: #1E293B; margin-bottom: 10px;">{title}</h3>
        <p style="font-size: 16px; max-width: 500px; margin: 0 auto;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def render_loading_state(message: str):
    """
    Renders a custom loading block.
    """
    with st.spinner(message):
        st.empty()
