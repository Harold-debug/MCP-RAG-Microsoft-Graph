#!/usr/bin/env python3
"""
Comprehensive diagnostic script to identify authentication issues.
"""

import requests
import json
import msal
from src.utils.config import get_config_value

def check_azure_app_config():
    """Check Azure AD app configuration."""
    print("🔍 Checking Azure AD App Configuration...")
    
    client_id = get_config_value("AZURE_CLIENT_ID")
    tenant_id = get_config_value("AZURE_TENANT_ID")
    
    print(f"✅ Client ID: {client_id}")
    print(f"✅ Tenant ID: {tenant_id}")
    
    # Check app registration endpoint
    try:
        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": "http://localhost:8501",
            "scope": "https://graph.microsoft.com/User.Read",
            "response_mode": "query"
        }
        
        response = requests.get(url, params=params, allow_redirects=False)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if 'error' in location:
                print(f"❌ Error in redirect: {location}")
            else:
                print("✅ Redirect is working")
        else:
            print(f"❌ Unexpected response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

def test_device_flow():
    """Test device code flow directly."""
    print("\n🔍 Testing Device Code Flow...")
    
    client_id = get_config_value("AZURE_CLIENT_ID")
    tenant_id = get_config_value("AZURE_TENANT_ID")
    
    # Create MSAL app
    app = msal.PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}"
    )
    
    scopes = [
        "https://graph.microsoft.com/User.Read",
        "https://graph.microsoft.com/Sites.Read.All",
        "https://graph.microsoft.com/Files.Read.All",
        "https://graph.microsoft.com/Mail.Read"
    ]
    
    try:
        # Test device flow
        flow = app.initiate_device_flow(scopes)
        
        if "user_code" not in flow:
            print("❌ Failed to create device flow")
            return False
            
        print(f"✅ Device flow created successfully")
        print(f"✅ User code: {flow['user_code']}")
        print(f"✅ Verification URI: {flow['verification_uri']}")
        print(f"✅ Expires in: {flow['expires_in']} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in device flow: {e}")
        return False

def check_permissions():
    """Check if the app has the right permissions."""
    print("\n🔍 Checking App Permissions...")
    
    client_id = get_config_value("AZURE_CLIENT_ID")
    tenant_id = get_config_value("AZURE_TENANT_ID")
    
    print("Required Microsoft Graph permissions:")
    print("  - User.Read")
    print("  - Sites.Read.All")
    print("  - Files.Read.All") 
    print("  - Mail.Read")
    
    print(f"\n📋 To check your app permissions:")
    print(f"1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/{client_id}")
    print("2. Click on 'API permissions' in the left menu")
    print("3. Verify these permissions are listed and granted:")
    print("   - Microsoft Graph > Delegated > User.Read")
    print("   - Microsoft Graph > Delegated > Sites.Read.All")
    print("   - Microsoft Graph > Delegated > Files.Read.All")
    print("   - Microsoft Graph > Delegated > Mail.Read")
    print("4. If permissions are missing, click 'Add a permission'")
    print("5. If permissions show 'Not granted', click 'Grant admin consent'")

def check_redirect_uris():
    """Check redirect URI configuration."""
    print("\n🔍 Checking Redirect URI Configuration...")
    
    client_id = get_config_value("AZURE_CLIENT_ID")
    
    print("Your app should have these redirect URIs configured:")
    print("  - http://localhost:8501 (for Streamlit)")
    print("  - urn:ietf:wg:oauth:2.0:oob (for device code flow)")
    
    print(f"\n📋 To check your redirect URIs:")
    print(f"1. Go to: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Overview/appId/{client_id}")
    print("2. Click on 'Authentication' in the left menu")
    print("3. Under 'Platform configurations', check:")
    print("   - Mobile and desktop applications")
    print("   - Redirect URIs should include the above URLs")
    print("4. If missing, add them and save")

def main():
    """Run all diagnostics."""
    print("🧪 Running Authentication Diagnostics...")
    print("=" * 50)
    
    check_azure_app_config()
    test_device_flow()
    check_permissions()
    check_redirect_uris()
    
    print("\n" + "=" * 50)
    print("📋 Summary of potential issues:")
    print("1. Missing or incorrect API permissions")
    print("2. Missing redirect URIs")
    print("3. App not configured for device code flow")
    print("4. Tenant restrictions or policies")
    print("5. App registration not properly configured")
    
    print("\n🔧 Next steps:")
    print("1. Check your Azure AD app configuration using the links above")
    print("2. Ensure all required permissions are granted")
    print("3. Add missing redirect URIs if needed")
    print("4. Try the authentication again")

if __name__ == "__main__":
    main()
