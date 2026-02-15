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
        # Full Zodiac Guide
        zodiac_guide = """
【⚠️自分の干支がわからない方へ⚠️】
生まれた年でチェック！👇

🐭 子年 (ねずみ): 1996, 2008, 2020, 2032
🐮 丑年 (うし): 1997, 2009, 2021, 2033
🐯 寅年 (とら): 1998, 2010, 2022, 2034
🐰 卯年 (うさぎ): 1999, 2011, 2023, 2035
🐲 辰年 (たつ): 2000, 2012, 2024, 2036
🐍 巳年 (へび): 2001, 2013, 2025, 2037
🐴 午年 (うま): 2002, 2014, 2026, 2038
🐑 未年 (ひつじ): 2003, 2015, 2027, 2039
🐵 申年 (さる): 2004, 2016, 2028, 2040
🐔 酉年 (とり): 2005, 2017, 2029, 2041
🐶 戌年 (いぬ): 2006, 2018, 2030, 2042
🐗 亥年 (いのしし): 2007, 2019, 2031, 2043
"""

        desc = f"""
{eto_kanji}年の皆さん、今日の運勢をお届けします！🔮

🎯 動画の内容:
- 今日の総合運勢と開運アドバイス
- 恋愛運・仕事運・金運の完全予報
- 今すぐできるラッキーアクション

📍 今日のポイント:
💕 恋愛運 - パートナーとの関係が深まるチャンス
💼 仕事運 - 午後から運気が上昇
💰 金運 - 臨時収入の予感あり
🍀 ラッキーアイテム - 動画をチェック！

👇 自分の干支がわからない方はコメント欄で質問してね！

📺 毎日更新中！フォローして最新運勢をGET！

#shorts #占い #今日の運勢 #干支占い #{eto_kanji}年 #運勢 #スピリチュアル #開運 #ラッキーカラー #恋愛運 #仕事運 #金運 #Japanese #fortune #zodiac #horoscope #viral #trending #子年占い #友引 #金運対策 #開運術 #三碧木星 #節分運勢 #水の相性 #運気アップ #占い好きな人と繋がりたい #2026年運勢 #救済動画

{zodiac_guide}
        """.strip()

        # --- TAGS (High-Volume Japanese Keywords) ---
        tags = [
            "shorts", "占い", "今日の運勢", "干支占い", f"{eto_kanji}年", "運勢", 
            "スピリチュアル", "開運", "ラッキーカラー", "恋愛運", "仕事運", "金運", 
            "daily horoscope", "Japanese horoscope", "zodiac", "fortune telling", 
            "viral", "trending", "子年占い", "友引", "金運対策", "開運術", 
            "三碧木星", "節分運勢", "水の相性", "運気アップ", "占い好きな人と繋がりたい", 
            "2026年運勢", "救済動画"
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
                    print(f"      📤 Uploading... {progress}%", flush=True)
            
            video_id = response.get("id")
            self.logger.info(f"✅ Upload Complete! Video ID: {video_id}")
            self.logger.info(f"   URL: https://youtube.com/shorts/{video_id}")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"❌ Upload Failed: {e}")
            self.logger.error(f"   Full traceback:\n{traceback.format_exc()}")
            return False
