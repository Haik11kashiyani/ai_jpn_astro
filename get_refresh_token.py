from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

def get_refresh_token():
    """
    Runs a local web server to authorize the app and get a Refresh Token.
    Requires 'client_secret.json' in the same folder.
    """
    
    if not os.path.exists('client_secret.json'):
        print("❌ Error: 'client_secret.json' not found!")
        print("   Please download it from Google Cloud Console (OAuth 2.0 Client IDs)")
        return

    # Scopes needed for uploading
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', SCOPES)
        
        print("🌍 Opening browser for authorization...")
        creds = flow.run_local_server(port=0)

        print("\n✅ Authorization Successful!")
        print("="*60)
        print(f"REFRESH TOKEN: {creds.refresh_token}")
        print("="*60)
        print("Copy this token and add it to your GitHub Secrets as: YOUTUBE_REFRESH_TOKEN")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    get_refresh_token()
