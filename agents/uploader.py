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
    Optimized for Japanese Eto Fortune content (#shorts viral strategy).
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
                None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.service = build('youtube', 'v3', credentials=creds)
            self.logger.info("✅ YouTube Authenticated Successfully.")
        except Exception as e:
            self.logger.error(f"❌ YouTube Auth Failed: {e}")

    def generate_metadata(self, eto_name: str, date_str: str, period_type: str = "Daily", eto_info: dict = None) -> dict:
        """
        Generates Viral-Optimized Japanese YouTube Metadata.
        Dynamic and content-specific for maximum CTR.
        """
        # Eto Kanji mapping
        ETO_KANJI = {
            "ne": "子", "rat": "子",
            "ushi": "丑", "ox": "丑",
            "tora": "寅", "tiger": "寅",
            "u": "卯", "rabbit": "卯",
            "tatsu": "辰", "dragon": "辰",
            "mi": "巳", "snake": "巳",
            "uma": "午", "horse": "午",
            "hitsuji": "未", "sheep": "未",
            "saru": "申", "monkey": "申",
            "tori": "酉", "rooster": "酉",
            "inu": "戌", "dog": "戌",
            "i": "亥", "boar": "亥"
        }
        
        clean_key = eto_name.split('(')[0].strip().lower()
        eto_kanji = ETO_KANJI.get(clean_key, eto_name)
        
        if eto_info:
            eto_kanji = eto_info.get("kanji", eto_kanji)
        
        # Dynamic Title Hooks (rotated for variety)
        title_hooks = [
            f"🔥 {eto_kanji}年さん今日は絶好調！",
            f"💕 {eto_kanji}年の恋愛運が急上昇！",
            f"💰 {eto_kanji}年に金運の波が来る！",
            f"⚠️ {eto_kanji}年さん要注意！でも大丈夫",
            f"✨ {eto_kanji}年に奇跡のチャンス到来",
            f"🌟 {eto_kanji}年おめでとう！大吉の日",
            f"😱 {eto_kanji}年さん見ないと後悔！",
        ]
        
        # Select based on date for consistency
        import hashlib
        hash_val = int(hashlib.md5(f"{eto_name}{date_str}".encode()).hexdigest(), 16)
        selected_hook = title_hooks[hash_val % len(title_hooks)]
        
        # --- TITLE (MUST include #shorts) ---
        if period_type == "Daily":
            title = f"{selected_hook} 🔮 #shorts"
        elif period_type == "Monthly":
            title = f"📅 {eto_kanji}年 {date_str}月間運勢 大公開！ #shorts"
        elif period_type == "Yearly":
            # Extract year from date_str
            year = date_str if date_str.isdigit() else "2026"
            title = f"🎆 {eto_kanji}年の{year}年運勢が凄すぎる！ #shorts"
        else:
            title = f"🔮 {eto_kanji}年 開運アドバイス {date_str} #shorts"
        
        # Ensure under 80 chars
        if len(title) > 80:
            title = title[:76] + "... #shorts"
        
        # --- DESCRIPTION ---
        # Generate Birth Year Table for Description
        current_year = datetime.now().year
        birth_year_table = ""
        # Simple lookup for last ~2 cycles
        # Rat is 2020, 2008, 1996...
        # Calculate years for this specific Eto
        target_years = []
        # Base years for 20th/21st century
        base_years = {
            "rat": 2020, "ox": 2021, "tiger": 2022, "rabbit": 2023, 
            "dragon": 2024, "snake": 2025, "horse": 2026, "sheep": 2027, 
            "monkey": 2028, "rooster": 2029, "dog": 2030, "boar": 2031
        }
        
        base = base_years.get(clean_key.split()[0], 2020)
        # Adjust base to be in past
        while base > current_year:
            base -= 12
        
        for i in range(5):
            target_years.append(str(base - (i * 12)))
        
        year_list = ", ".join(sorted(target_years))

        desc = f"""
{eto_kanji}年の皆さん、今日の運勢をお届けします！🔮

🎯 あなたは{eto_kanji}年生まれ？(生まれ年チェック):
{year_list}, ...

📍 今日のポイント:
💕 恋愛運 - パートナーとの関係が深まるチャンス
💼 仕事運 - 午後から運気が上昇
💰 金運 - 臨時収入の予感あり
🍀 ラッキーアイテム - 動画をチェック！

👇 自分の干支がわからない方はコメント欄で質問してね！

📺 毎日更新中！フォローして最新運勢をGET！

#shorts #占い #今日の運勢 #干支占い #{eto_kanji}年 #運勢 #スピリチュアル #開運 #ラッキーカラー #恋愛運 #仕事運 #金運 #Japanese #fortune #zodiac #horoscope #viral #trending
        """.strip()

        # --- TAGS (High-Volume Japanese Keywords) ---
        tags = [
            "shorts",                    # CRITICAL for Shorts algorithm
            "占い",                      # Fortune telling
            "今日の運勢",                # Today's fortune
            "干支占い",                  # Eto zodiac fortune
            f"{eto_kanji}年",           # Specific animal year
            "運勢",                      # Fortune/luck
            "スピリチュアル",            # Spiritual
            "開運",                      # Fortune improvement
            "ラッキーカラー",            # Lucky color
            "恋愛運",                    # Love fortune
            "仕事運",                    # Work fortune
            "金運",                      # Money fortune
            "daily horoscope",           # English for wider reach
            "Japanese horoscope",
            "zodiac",
            "fortune telling",
            "viral",
            "trending"
        ]
        
        return {
            "title": title,
            "description": desc,
            "tags": tags,
            "categoryId": "24"  # Entertainment
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
