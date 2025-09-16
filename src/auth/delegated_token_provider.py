import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List

import msal
import streamlit as st


logger = logging.getLogger(__name__)


class DelegatedTokenProvider:
    """Acquire and refresh Microsoft Graph access tokens using MSAL (delegated)."""

    def __init__(self, client_id: str, authority: str, scopes: List[str]):
        self.client_id = client_id
        self.authority = authority
        self.scopes = scopes
        self.app = msal.PublicClientApplication(client_id, authority=authority)

    def _extract_expiry(self, result: dict) -> Optional[datetime]:
        # Prefer expires_on (epoch or string), fallback to expires_in seconds
        try:
            if "expires_on" in result:
                expires_on_val = result["expires_on"]
                # msal may return string epoch
                epoch = int(expires_on_val)
                return datetime.fromtimestamp(epoch)
            if "expires_in" in result:
                return datetime.utcnow() + timedelta(seconds=int(result["expires_in"]))
        except Exception:
            pass
        # Default to 55 minutes from now if unknown
        return datetime.utcnow() + timedelta(minutes=55)

    def get_token(self, force_refresh: bool = False) -> Tuple[Optional[str], Optional[datetime]]:
        """Get an access token and expiry; uses silent first, then device code.

        Returns (token, expires_on_utc)
        """
        try:
            accounts = [] if force_refresh else self.app.get_accounts()
            if accounts and not force_refresh:
                result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    return result["access_token"], self._extract_expiry(result)

            # Device code flow for Streamlit environments
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            if "user_code" not in flow:
                st.error("Failed to start device flow")
                return None, None
            st.info("🔐 Device Code Authentication Required")
            st.info(f"Code: {flow['user_code']}")
            st.info(f"URL: {flow['verification_uri']}")
            result = self.app.acquire_token_by_device_flow(flow)
            print("result, here is the result:: ", result)
            if result and "access_token" in result:
                st.success("✅ Authentication successful!")
                return result["access_token"], self._extract_expiry(result)
            if result and "error" in result:
                st.error(f"Auth failed: {result.get('error_description', 'Unknown error')}")
                return None, None
            return None, None
        except Exception as e:
            logger.error("MSAL error getting token: %s", str(e))
            st.error(f"Failed to acquire token: {str(e)}")
            return None, None

    def force_refresh(self) -> Tuple[Optional[str], Optional[datetime]]:
        return self.get_token(force_refresh=True)


