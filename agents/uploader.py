import os
import json
import logging
import random
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    """
    Handles YouTube Authentication and Video Uploads.
    Uses Refresh Token flow for headless automation.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.service = None
        
        if self.client_id and self.client_secret and self.refresh_token:
            self._authenticate()
        else:
            self.logger.warning("⚠️ YouTube Credentials missing! Uploads will fail.")

    def _authenticate(self):
        """Authenticates using the refresh token."""
        try:
            creds = Credentials(
                None, # No access token initially
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.service = build('youtube', 'v3', credentials=creds)
            self.logger.info("✅ YouTube Authenticated Successfully.")
        except Exception as e:
            self.logger.error(f"❌ YouTube Auth Failed: {e}")

    def generate_metadata(self, rashi_name: str, date_str: str, period_type: str = "Daily") -> dict:
        """
        Generates Viral-Optimized Title, Description, and Tags.
        """
        # Hindi Rashi names for SEO
        RASHI_HINDI = {
            "mesh": "मेष", "aries": "मेष",
            "vrushabh": "वृषभ", "taurus": "वृषभ", 
            "mithun": "मिथुन", "gemini": "मिथुन",
            "kark": "कर्क", "cancer": "कर्क",
            "singh": "सिंह", "leo": "सिंह", 
            "kanya": "कन्या", "virgo": "कन्या",
            "tula": "तुला", "libra": "तुला", 
            "vrushchik": "वृश्चिक", "scorpio": "वृश्चिक",
            "dhanu": "धनु", "sagittarius": "धनु", 
            "makar": "मकर", "capricorn": "मकर", 
            "kumbh": "कुंभ", "aquarius": "कुंभ",
            "meen": "मीन", "pisces": "मीन"
        }
        
        clean_key = rashi_name.split('(')[0].strip().lower()
        hindi_name = RASHI_HINDI.get(clean_key, rashi_name)
        
        # Extract year dynamically from date_str
        import re
        year_match = re.search(r'\\b(20\\d{2})\\b', date_str)
        dynamic_year = year_match.group(1) if year_match else date_str
        
        # Clean rashi name for shorter title (no parentheses)
        clean_rashi = rashi_name.split('(')[0].strip()
        
        # --- TITLE STRATEGY (Under 100 chars) ---
        if period_type == "Daily":
            title = f"{hindi_name} Rashifal {date_str} 🔮 #shorts #viral"
        elif period_type == "Monthly":
            title = f"{hindi_name} Monthly Rashifal {date_str} 📅 #shorts #viral"
        else: # Yearly
            title = f"{hindi_name} Yearly Horoscope {dynamic_year} ⭐ #shorts #viral"
            
        # Ensure legal length (keep hashtags at end)
        if len(title) > 100:
            title = title[:85] + "... #shorts #viral"

        # --- DESCRIPTION STRATEGY ---
        desc = f"""
{hindi_name} Rashifal {period_type} Prediction for {date_str}.
😱 Watch this before starting your day!
Knowing your astrology can help you plan your career, love, and money better.

🔮 **Topics Covered:**
- Love & Relationships
- Career & Business
- Money & Finance
- Health & Wellness
- Lucky Color & Number

#shorts #viral #astrology #rashifal #{clean_key} #{hindi_name} #horoscope #jyotish #dailyhoroscope #lzodiac #trending #ytshorts
        """.strip()

        # --- TAGS STRATEGY ---
        tags = [
            f"{hindi_name} rashifal", 
            f"{clean_key} horoscope",
            "daily horoscope",
            "aaj ka rashifal",
            "astrology",
            "shorts",
            "viral",
            "jyotish",
            "bhavishyafal",
            f"{hindi_name} {date_str}",
            "zodiac signs",
            "trending",
            "ytshorts",
            "astrology 2025"
        ]
        
        return {
            "title": title,
            "description": desc,
            "tags": tags,
            "categoryId": "24" # Entertainment
        }

    def upload_video(self, file_path: str, metadata: dict, privacy_status: str = "public", publish_at: datetime = None):
        """Uploads the video. Supports scheduled publishing."""
        if not self.service:
            self.logger.error("❌ Cannot upload: Not Authenticated.")
            return False

        if not os.path.exists(file_path):
            self.logger.error(f"❌ File not found: {file_path}")
            return False

        self.logger.info(f"🚀 Uploading {file_path}...")
        self.logger.info(f"   Title: {metadata['title']}")
        
        status_body = {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
        
        # Handle Scheduling
        if publish_at:
            # Format: '2024-12-25T07:00:00.000Z' (RFC 3339)
            # YouTube requires 'private' status for scheduled videos
            status_body["privacyStatus"] = "private"
            status_body["publishAt"] = publish_at.isoformat() + "Z" 
            self.logger.info(f"   📅 Scheduled for: {status_body['publishAt']}")

        body = {
            "snippet": {
                "title": metadata['title'],
                "description": metadata['description'],
                "tags": metadata['tags'],
                "categoryId": metadata['categoryId']
            },
            "status": status_body
        }

        try:
            # Resumable upload for safety
            media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"      📤 Uploading... {progress}%")
            
            video_id = response.get("id")
            self.logger.info(f"✅ Upload Complete! Video ID: {video_id}")
            self.logger.info(f"   URL: https://youtube.com/shorts/{video_id}")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"❌ Upload Failed: {e}")
            self.logger.error(f"   Full traceback:\n{traceback.format_exc()}")
            return False
