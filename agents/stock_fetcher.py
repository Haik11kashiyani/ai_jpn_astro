import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StockFetcher:
    """
    Fetches high-quality stock video from Pexels API.
    Smart selection: picks the BEST matching video based on quality score.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            logging.warning("⚠️ PEXELS_API_KEY missing. Stock fetch will fail.")
        
        self.headers = {"Authorization": self.api_key} if self.api_key else {}
        self.download_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "footage")
        os.makedirs(self.download_dir, exist_ok=True)

    def _score_video(self, video: dict, min_duration: int) -> float:
        """
        Score a video based on quality factors.
        Higher score = better video.
        """
        score = 0.0
        
        # Duration score (prefer videos that fit our needs)
        duration = video.get("duration", 0)
        if duration >= min_duration:
            score += 30  # Meets minimum
            if duration <= min_duration * 2:
                score += 20  # Not too long (easier to trim)
        else:
            score -= 50  # Too short
        
        # Resolution score
        video_files = video.get("video_files", [])
        max_height = max((f.get("height", 0) for f in video_files), default=0)
        if max_height >= 1080:
            score += 40  # Full HD
        elif max_height >= 720:
            score += 20  # HD
        
        # Popularity indicators
        # Note: Pexels doesn't give views but files count can indicate quality
        if len(video_files) >= 4:
            score += 10  # Multiple quality options = professionally processed
        
        return score

    def search_video(self, query: str, orientation: str = "portrait", min_duration: int = 5) -> str:
        """
        Search and download the BEST video matching the query.
        Uses smart scoring to pick the highest quality, most relevant video.
        Returns local file path or None.
        """
        if not self.api_key:
            logging.error("❌ No Pexels Key")
            return None
            
        logging.info(f"🔍 Searching Pexels for: '{query}'")
        
        # Fetch more videos for better selection
        url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=15"
        
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            
            if not data.get("videos"):
                logging.warning(f"   ❌ No videos found for '{query}'")
                # Try with simpler query
                simple_query = query.split()[0] if " " in query else query
                url = f"https://api.pexels.com/videos/search?query={simple_query}&orientation={orientation}&per_page=10"
                response = requests.get(url, headers=self.headers)
                data = response.json()
                if not data.get("videos"):
                    return None
            
            # Score all videos and pick the best one
            videos = data["videos"]
            scored_videos = []
            
            for video in videos:
                score = self._score_video(video, min_duration)
                scored_videos.append((score, video))
            
            # Sort by score descending
            scored_videos.sort(key=lambda x: x[0], reverse=True)
            
            # Pick the best one
            best_score, video = scored_videos[0]
            logging.info(f"   🎯 Best match: {video['id']} (score: {best_score})")
            
            # Get best quality video file (prefer 1080p for balance of quality/size)
            video_files = video["video_files"]
            
            # Sort by height descending
            video_files.sort(key=lambda x: x.get("height", 0), reverse=True)
            
            # Prefer 1080p, fallback to highest available
            selected_file = None
            for f in video_files:
                if f.get("height") == 1080:
                    selected_file = f
                    break
            
            if not selected_file:
                # Get highest quality available
                selected_file = video_files[0] if video_files else None
            
            if not selected_file:
                logging.error("   ❌ No downloadable file found")
                return None
            
            download_url = selected_file["link"]
            
            # Filename with video ID to cache
            safe_query = query.replace(" ", "_")[:20]
            filename = f"{safe_query}_{video['id']}.mp4"
            filepath = os.path.join(self.download_dir, filename)
            
            # Check if exists (cached)
            if os.path.exists(filepath):
                logging.info(f"   ✅ Cached: {filename}")
                return filepath
            
            # Download
            res_info = f"{selected_file.get('width', '?')}x{selected_file.get('height', '?')}"
            logging.info(f"   ⬇️ Downloading {video['id']} ({res_info})...")
            
            with requests.get(download_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            logging.info(f"   ✅ Saved: {filename}")
            return filepath
            
        except Exception as e:
            logging.error(f"❌ Pexels Error: {e}")
            return None
