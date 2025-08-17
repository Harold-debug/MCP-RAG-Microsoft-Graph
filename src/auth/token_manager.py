import logging
import streamlit as st
import msal
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TokenManager:
    """Handles Azure AD authentication and token management."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the TokenManager with MSAL configuration.
        
        Args:
            config: Dictionary containing MSAL configuration parameters
        """
        try:
            self.config = config
            self.app = msal.PublicClientApplication(
                config["client_id"],
                authority=config["authority"]
            )
        except ValueError as e:
            error_msg = f"Failed to initialize MSAL: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            st.error("Please check your Azure AD configuration.")
            raise
        
    def get_token(self) -> Optional[str]:
        """
        Get an access token, either from cache or through interactive login.
        
        Returns:
            str: The access token if successful, None otherwise
        """
        try:
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(
                    self.config["scope"],
                    account=accounts[0]
                )
                if result:
                    return result['access_token']
            
            result = self.app.acquire_token_interactive(self.config["scope"])
            if "access_token" in result:
                return result['access_token']
            return None
            
        except Exception as e:
            error_msg = f"Failed to acquire token: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return None

    def clear_token_cache(self) -> None:
        """Clear all cached tokens."""
        accounts = self.app.get_accounts()
        for account in accounts:
            self.app.remove_account(account) 