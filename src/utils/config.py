import os
import streamlit as st
from typing import Optional
from dotenv import load_dotenv

# Load environment variables as fallback
load_dotenv()

def get_config_value(key: str, default: str = None) -> str:
    """
    Get configuration value from secrets.toml or environment variables.
    """
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

def get_graph_access_token_from_config() -> Optional[str]:
    """Return Microsoft Graph access token if present in configuration."""
    return get_config_value("MS_GRAPH_ACCESS_TOKEN")

def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "initialized" not in st.session_state:
        st.session_state.initialized = False