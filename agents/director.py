import os
import json
import logging
import re
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DirectorAgent:
    """
    The Director Agent converts a Japanese fortune script into a Visual Screenplay.
    Uses LOCAL keyword analysis — NO API calls needed.
    Focuses on authentic Japanese aesthetics: cherry blossoms, temples, zen gardens.
    """

    # Mood keywords mapping (Japanese text → mood)
    MOOD_KEYWORDS = {
        "energetic": ["大吉", "最高", "絶好調", "チャンス", "飛躍", "成功", "勝利", "パワー", "エネルギー", "情熱", "挑戦", "active", "energy"],
        "sakura": ["恋愛", "愛情", "ロマンス", "出会い", "パートナー", "結婚", "デート", "春", "桜", "花", "love", "romance"],
        "mystical": ["運命", "宿命", "神秘", "霊感", "直感", "予感", "転換", "変化", "秘密", "深い", "mystery", "destiny"],
        "serene": ["平和", "安定", "穏やか", "癒し", "休息", "バランス", "調和", "健康", "自然", "peace", "calm", "balance"],
        "zen": ["注意", "慎重", "控えめ", "反省", "忍耐", "仏滅", "凶", "警告", "caution", "careful"],
    }

    # Scene visual keywords for each fortune section
    SCENE_VISUALS = {
        "energetic": {
            "hook": "Sunrise over Mount Fuji golden light energy power",
            "love": "Festival lanterns couple warmth celebration",
            "career": "Tokyo skyline sunrise confidence ambition success",
            "money": "Golden coins flowing maneki-neko prosperity abundant",
            "health": "Martial arts dojo strength vitality morning exercise",
            "lucky_item": "Daruma doll shrine blessing fortune red",
        },
        "sakura": {
            "hook": "Cherry blossoms petals floating river romantic pink",
            "love": "Couple under cherry blossom tree sunset romantic",
            "career": "Japanese garden bridge new beginnings spring",
            "money": "Sakura petals golden light gentle prosperity",
            "health": "Onsen hot spring relaxation cherry blossom view",
            "lucky_item": "Omamori love charm shrine pink silk",
        },
        "mystical": {
            "hook": "Mystical torii gate fog moonlight ethereal spiritual",
            "love": "Full moon reflection lake mysterious encounter destiny",
            "career": "Ancient temple incense smoke transformation power",
            "money": "Treasure chest shrine mystical golden glow",
            "health": "Zen meditation candlelight inner peace spiritual",
            "lucky_item": "Crystal ball fortune teller mystical purple glow",
        },
        "serene": {
            "hook": "Peaceful bamboo forest morning mist gentle light",
            "love": "Quiet temple garden couple harmony gentle",
            "career": "Calm ocean sunrise steady progress patience",
            "money": "Flowing river coins gentle abundance natural",
            "health": "Zen garden raking sand meditation peaceful",
            "lucky_item": "Green tea ceremony harmony balance tradition",
        },
        "zen": {
            "hook": "Zen rock garden minimalist calm contemplation",
            "love": "Moonlit path shrine quiet reflection bond",
            "career": "Mountain path fog patience determination steady",
            "money": "Simple offering shrine coins gratitude modest",
            "health": "Bamboo water fountain zen garden meditation",
            "lucky_item": "Omamori charm shrine spiritual protection",
        },
    }

    def __init__(self, api_key: str = None, backup_key: str = None):
        """Initialize Director — no API keys needed for local analysis."""
        logging.info("🎬 Director: Initialized with LOCAL mood analysis (zero API calls).")

    def _detect_mood(self, text: str) -> str:
        """Detect mood from Japanese text using keyword matching."""
        text_lower = text.lower()
        scores = {}

        for mood, keywords in self.MOOD_KEYWORDS.items():
            score = 0
            for kw in keywords:
                # Count occurrences of each keyword
                count = text_lower.count(kw.lower()) if kw.isascii() else text.count(kw)
                score += count
            scores[mood] = score

        # Get mood with highest score, default to "zen"
        best_mood = max(scores, key=scores.get) if any(v > 0 for v in scores.values()) else "zen"
        return best_mood

    def create_screenplay(self, script_data) -> dict:
        """
        Analyzes the fortune script and generates Japanese-themed visual keywords.
        Uses LOCAL keyword analysis — NO API calls.
        """
        logging.info("🎬 Director: Creating Japanese visual screenplay (local analysis)...")

        sections = ["hook", "love", "career", "money", "health", "lucky_item"]

        # Extract text from script
        if isinstance(script_data, dict):
            full_script_text = " ".join(
                [str(script_data.get(k, "")) for k in sections if k in script_data]
            )
        elif isinstance(script_data, list):
            full_script_text = " ".join([str(item) for item in script_data if item])
        else:
            full_script_text = str(script_data)

        # Detect mood locally
        mood = self._detect_mood(full_script_text)
        logging.info(f"🎵 Director: Detected mood: {mood} (local analysis)")

        # Get visual keywords for the detected mood
        scenes = self.SCENE_VISUALS.get(mood, self.SCENE_VISUALS["zen"])

        result = {"mood": mood, "scenes": scenes}
        logging.info(f"✅ Director: Screenplay ready (zero API calls used).")
        return result
