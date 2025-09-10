#!/usr/bin/env python3
"""
Script to check Azure AD configuration and help diagnose authentication issues.
"""

import requests
import json
from src.utils.config import get_config_value

def check_azure_config():
    """Check Azure AD configuration."""
    print("🔍 Checking Azure AD Configuration...")
    
    client_id = get_config_value("AZURE_CLIENT_ID")
    tenant_id = get_config_value("AZURE_TENANT_ID")
    redirect_uri = get_config_value("AZURE_REDIRECT_URI", "http://localhost:8501")
    
    print(f"✅ Client ID: {client_id}")
    print(f"✅ Tenant ID: {tenant_id}")
    print(f"✅ Redirect URI: {redirect_uri}")
    
    # Check if we can access the Azure AD app registration
    try:
        # This is a public endpoint to check app registration
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "https://graph.microsoft.com/User.Read",
            "response_mode": "query"
        }
        
        print(f"\n🔗 Testing authentication URL:")
        print(f"URL: {url}")
        print(f"Parameters: {json.dumps(params, indent=2)}")
        
        # Make a test request
        response = requests.get(url, params=params, allow_redirects=False)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Redirect is working (this is expected)")
            location = response.headers.get('Location', '')
            print(f"Redirect Location: {location[:200]}...")
        else:
            print(f"❌ Unexpected response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
    
    print("\n📋 Troubleshooting Steps:")
    print("1. Check your Azure AD app registration:")
    print(f"   - Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/{client_id}")
    print("   - Verify the redirect URI is configured as: http://localhost:8501")
    print("   - Make sure it's set as 'Mobile and desktop applications'")
    print("   - Check that the required permissions are granted")
    
    print("\n2. Required Microsoft Graph permissions:")
    print("   - User.Read")
    print("   - Sites.Read.All") 
    print("   - Files.Read.All")
    print("   - Mail.Read")
    
    print("\n3. If redirect URI is wrong:")
    print("   - Add http://localhost:8501 to your app's redirect URIs")
    print("   - Remove any other localhost redirect URIs")
    print("   - Save the changes")

if __name__ == "__main__":
    check_azure_config()
