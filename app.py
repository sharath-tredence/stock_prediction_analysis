import streamlit as st
from ui import launch_app

if "mode" not in st.session_state:
    st.session_state.mode = "idle"  # idle | history | future

if __name__ == "__main__":
    launch_app()
