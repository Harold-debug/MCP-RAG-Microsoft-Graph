#!/usr/bin/env python3
"""
Alternative token manager using Azure CLI authentication.
This bypasses Azure AD app configuration issues.
"""

import subprocess
import json
import logging
import streamlit as st
from typing import Optional

logger = logging.getLogger(__name__)

class AzureCLITokenManager:
    """Handles Azure authentication using Azure CLI."""
    
    def __init__(self):
        """Initialize the Azure CLI token manager."""
        self.token = None
        
    def get_token(self) -> Optional[str]:
        """
        Get an access token using Azure CLI.
        
        Returns:
            str: The access token if successful, None otherwise
        """
        try:
            logger.info("Getting token using Azure CLI...")
            
            # Check if Azure CLI is installed and user is logged in
            try:
                # Get current account
                result = subprocess.run(
                    ["az", "account", "show"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                account_info = json.loads(result.stdout)
                logger.info(f"Logged in as: {account_info.get('user', {}).get('name', 'Unknown')}")
                
            except subprocess.CalledProcessError:
                st.error("❌ Azure CLI not installed or not logged in")
                st.info("Please install Azure CLI and run: az login")
                return None
            except FileNotFoundError:
                st.error("❌ Azure CLI not found")
                st.info("Please install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
                return None
            
            # Get access token for Microsoft Graph
            result = subprocess.run(
                [
                    "az", "account", "get-access-token",
                    "--resource", "https://graph.microsoft.com",
                    "--query", "accessToken",
                    "-o", "tsv"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            token = result.stdout.strip()
            if token:
                logger.info("✅ Successfully obtained token via Azure CLI")
                self.token = token
                return token
            else:
                logger.error("❌ No token received from Azure CLI")
                return None
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Azure CLI error: {e.stderr}"
            logger.error(error_msg)
            st.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Failed to get token: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            return None
    
    def clear_token_cache(self) -> None:
        """Clear the token cache."""
        self.token = None
        logger.info("Token cache cleared")
        
    def get_account_info(self) -> dict:
        """Get information about the current Azure account."""
        try:
            result = subprocess.run(
                ["az", "account", "show"],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
            
    def force_refresh_token(self) -> Optional[str]:
        """Force a token refresh."""
        logger.info("Forcing token refresh...")
        self.clear_token_cache()
        return self.get_token()
