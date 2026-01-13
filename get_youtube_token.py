"""
YouTube OAuth Token Generator
Run this script locally to get a new refresh token.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import json

# YouTube upload scope
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("=" * 50)
    print("YouTube OAuth Token Generator")
    print("=" * 50)
    
    # You need your client_secret.json file from Google Cloud Console
    # Download it from: APIs & Services > Credentials > Your OAuth Client > Download JSON
    
    CLIENT_ID = input("\nEnter your YOUTUBE_CLIENT_ID: ").strip()
    CLIENT_SECRET = input("Enter your YOUTUBE_CLIENT_SECRET: ").strip()
    
    # Create a temporary client config
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    
    # Save temp config
    with open("temp_client_config.json", "w") as f:
        json.dump(client_config, f)
    
    print("\n🌐 Opening browser for authentication...")
    print("   Please sign in with your YouTube channel account.\n")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            "temp_client_config.json",
            scopes=SCOPES
        )
        
        # This will open a browser window
        credentials = flow.run_local_server(port=8090)
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Here's your new refresh token:")
        print("=" * 50)
        print(f"\nREFRESH_TOKEN:\n{credentials.refresh_token}")
        print("\n" + "=" * 50)
        print("\n📝 Now update your GitHub Secret:")
        print("   1. Go to: GitHub Repo → Settings → Secrets and variables → Actions")
        print("   2. Edit 'YOUTUBE_REFRESH_TOKEN'")
        print("   3. Paste the refresh token above")
        print("   4. Save!")
        print("\n🎉 Done! Your automation will now work without token expiry.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're signed into the correct Google account")
        print("2. Check that your Client ID and Secret are correct")
    
    finally:
        # Cleanup
        import os
        if os.path.exists("temp_client_config.json"):
            os.remove("temp_client_config.json")

if __name__ == "__main__":
    main()
