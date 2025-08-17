import os
import streamlit as st
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables as fallback
load_dotenv()

def get_config_value(key: str, default: str = None) -> str:
    """
    Get configuration value from secrets.toml or environment variables.
    
    Args:
        key: The configuration key to look up
        default: Default value if key is not found
        
    Returns:
        str: The configuration value
    """
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

def load_msal_config() -> Dict[str, Any]:
    """
    Load MSAL configuration from secrets.toml or environment variables.
    
    Returns:
        Dict[str, Any]: MSAL configuration dictionary
    """
    return {
        "client_id": get_config_value("AZURE_CLIENT_ID"),
        "authority": f"https://login.microsoftonline.com/{get_config_value('AZURE_TENANT_ID')}",
        "scope": ["https://graph.microsoft.com/.default"],
        "redirect_uri": get_config_value("AZURE_REDIRECT_URI", "http://localhost:8501")
    }

def check_required_vars() -> List[str]:
    """
    Check for required configuration variables.
    
    Returns:
        List[str]: List of missing required variables
    """
    required_vars = ["AZURE_CLIENT_ID", "AZURE_TENANT_ID"]
    return [var for var in required_vars if not get_config_value(var)]

def init_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    if "last_token_refresh" not in st.session_state:
        st.session_state.last_token_refresh = None 