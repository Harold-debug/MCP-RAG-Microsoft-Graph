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
        Get an access token, either from cache or through device code flow.
        
        Returns:
            str: The access token if successful, None otherwise
        """
        try:
            # Define the scopes properly - Microsoft Graph scopes only
            graph_scopes = self.config["scope"]
            
            # First try to get token silently from cache
            accounts = self.app.get_accounts()
            if accounts:
                logger.info(f"Found {len(accounts)} cached account(s), attempting silent token acquisition...")
                result = self.app.acquire_token_silent(
                    graph_scopes,
                    account=accounts[0]
                )
                if result and "access_token" in result:
                    logger.info("Successfully acquired token silently from cache")
                    return result['access_token']
                elif result and "error" in result:
                    logger.warning(f"Silent token acquisition failed: {result.get('error_description', 'Unknown error')}")
                    # Clear the problematic account and try device code
                    self.app.remove_account(accounts[0])
                    accounts = []
            
            # If no cached account or silent acquisition failed, try device code flow
            if not accounts:
                logger.info("No cached accounts found, starting device code authentication...")
                try:
                    # Use device code flow which is more reliable for desktop apps
                    flow = self.app.initiate_device_flow(graph_scopes)
                    
                    if "user_code" not in flow:
                        error_msg = "Failed to create device flow"
                        logger.error(error_msg)
                        st.error(error_msg)
                        return None
                    
                    # Display the device code to the user
                    st.info("🔐 **Device Code Authentication Required**")
                    st.info(f"**Code:** {flow['user_code']}")
                    st.info(f"**URL:** {flow['verification_uri']}")
                    st.info("Please enter this code in your browser to authenticate.")
                    
                    # Wait for the user to complete authentication
                    result = self.app.acquire_token_by_device_flow(flow)
                    
                    if "access_token" in result:
                        logger.info("Successfully acquired token through device code authentication")
                        st.success("✅ Authentication successful!")
                        return result['access_token']
                    elif "error" in result:
                        error_msg = f"Device code authentication failed: {result.get('error_description', 'Unknown error')}"
                        logger.error(error_msg)
                        st.error(error_msg)
                        return None
                    else:
                        logger.warning("Device code authentication completed but no token received")
                        return None
                        
                except Exception as e:
                    logger.error(f"Exception during device code authentication: {e}")
                    st.error(f"Authentication error: {str(e)}")
                    return None
            
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
        logger.info("Token cache cleared")
        
    def get_account_info(self) -> Dict[str, Any]:
        """Get information about the current account."""
        accounts = self.app.get_accounts()
        if accounts:
            return {
                "username": accounts[0].get("username"),
                "home_account_id": accounts[0].get("home_account_id"),
                "environment": accounts[0].get("environment")
            }
        return {}
        
    def force_refresh_token(self) -> Optional[str]:
        """Force a token refresh by clearing cache and re-authenticating."""
        logger.info("Forcing token refresh...")
        self.clear_token_cache()
        return self.get_token() 