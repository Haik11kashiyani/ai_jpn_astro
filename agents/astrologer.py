import os
import re
import json
import time
import logging
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

OPENROUTER_GEMINI_FREE = "google/gemini-2.0-flash-exp:free"

# ── Per-key quota tracking (shared across instances in the same process) ──
_google_exhausted_keys = set()   # indices of daily-exhausted Google AI keys
_openrouter_daily_exhausted = False
_last_google_call_ts = 0.0       # timestamp of most recent Google AI call

MIN_GOOGLE_CALL_INTERVAL = 8     # seconds between consecutive Google AI calls


def _is_daily_quota_error(error_str: str) -> bool:
    """Check if the 429 error indicates a DAILY quota exhaustion (not just per-minute)."""
    return any(x in error_str for x in ("PerDay", "limit: 0", "free_tier"))


def _is_rate_limit_error(error_str: str) -> bool:
    """Check if the error is any kind of rate limit (429)."""
    return "429" in error_str or "rate limit" in error_str.lower() or "quota exceeded" in error_str.lower() or "Quota exceeded" in error_str


def _parse_retry_seconds(error_str: str) -> int:
    """Parse the retry delay suggested by the API. Returns seconds to wait."""
    # Try 'retry in Xs' pattern
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str, re.I)
    if m:
        return min(int(float(m.group(1))) + 5, 180)
    # Try 'seconds: N' pattern from protobuf
    m = re.search(r'seconds["\s:]+\s*(\d+)', error_str)
    if m:
        return min(int(m.group(1)) + 5, 180)
    return 0


def _rate_limit_pre_call():
    """Enforce minimum spacing between Google AI calls to stay under per-minute limits."""
    global _last_google_call_ts
    elapsed = time.time() - _last_google_call_ts
    if elapsed < MIN_GOOGLE_CALL_INTERVAL:
        wait = MIN_GOOGLE_CALL_INTERVAL - elapsed
        logging.info(f"⏱️  Pre-call cooldown: waiting {wait:.1f}s before Google AI call...")
        time.sleep(wait)
    _last_google_call_ts = time.time()


# Try to import Google AI
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AstrologerAgent:
    """
    The Astrologer Agent generates authentic Japanese Eto (干支) Fortune content.
    Uses traditional systems: Eto, Kyusei Kigaku, Rokuyo, Gogyou (Five Elements).
    Acts as 星野先生 (Hoshino-sensei), a renowned Japanese fortune teller.
    """

    def _deep_cache_path(self, date_str: str) -> str:
        safe = (
            date_str.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .strip("-")
        )
        return os.path.join("cache", "almanac", f"{safe}.json")

    def derive_daily_parameters(self, date_str: str) -> dict:
        """
        Uses LLM to derive 100% ACCURATE traditional parameters (Rokuyo, Kyusei, Solar Term).
        Replaces simple arithmetic approximations with 'Deep Astrology' knowledge.
        Same for all 12 eto signs — cached per date to save API quota.
        """
        cache_path = self._deep_cache_path(date_str)
        if os.path.isfile(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                logging.info(f"📦 Using cached Deep Almanac for {date_str} (no API call)")
                return cached
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"⚠️ Almanac cache corrupt, regenerating: {e}")

        logging.info(f"🌌 Deep Astrology: Deriving exact parameters for {date_str}...")
        
        system_prompt = """
        You are an expert Japanese Astrologer/Almanac (暦).
        Your Job: Provide the EXACT traditional Japanese calendar data for a specific date.
        
        REQUIRED DATA:
        1. Exact Rokuyo (六曜) - based on the old lunar calendar.
        2. Kyusei (九星) - Daily flying star.
        3. Solar Term (二十四節気) - If applicable (e.g., Risshun, Geshi).
        4. 12 Choku (十二直) - e.g., Mitsu, Tairu.
        
        Return JSON ONLY.
        """
        
        user_prompt = f"""
        Get the Japanese Almanac data for: {date_str}

        Return JSON format:
        {{
            "rokuyo": {{ "name": "...", "reading": "...", "meaning": "..." }},
            "kyusei": {{ "name": "...", "element": "..." }},
            "sekki": "Solar Term or null",
            "choku": {{ "name": "...", "meaning": "..." }}
        }}
        """
        
        try:
            result = self._generate_script(
                "System", date_str, "Deep_Data", system_prompt, user_prompt
            )
            if result:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logging.info(f"💾 Cached Deep Almanac → {cache_path}")
            return result
        except Exception as e:
            logging.warning(f"⚠️ Deep Astrology Data failed: {e}. Falling back to standard calc.")
            return None

    def _get_trending_tags(self) -> str:
        """Returns current viral/trending tags for Japan."""
        # Mix of user-provided viral tags + standard astrology tags
        return "#子年占い #友引 #今日の運勢 #金運対策 #恋愛運 #開運術 #干支占い #三碧木星 #節分運勢 #水の相性 #運気アップ #占い好きな人と繋がりたい #スピリチュアル #2026年運勢 #救済動画 #shorts #fyp #viral #japan #trending #鑑定 #開運 #引き寄せ #予言 #最新"

    def _get_zodiac_guide(self) -> str:
        """Returns the How-To-Find-Zodiac text block."""
        return """
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

    def __init__(self, api_key: str = None, backup_key: str = None):
        """Initialize with OpenRouter API Keys (primary + backup) + multiple Google AI keys."""
        # ── OpenRouter Keys ──
        self.api_keys = []
        
        primary = api_key or os.getenv("OPENROUTER_API_KEY")
        if primary:
            self.api_keys.append(primary)
        
        backup = backup_key or os.getenv("OPENROUTER_API_KEY_BACKUP")
        if backup:
            self.api_keys.append(backup)
        
        backup2 = os.getenv("OPENROUTER_API_KEY_BACKUP_2")
        if backup2:
            self.api_keys.append(backup2)
        
        # ── Google AI Keys (support multiple for quota rotation) ──
        self.google_ai_keys = []
        
        for suffix in ['', '_2', '_3', '_4', '_5']:
            key = os.getenv(f"GOOGLE_AI_API_KEY{suffix}")
            if key:
                self.google_ai_keys.append(key)
        
        if not self.google_ai_keys:
            logging.warning("⚠️ No GOOGLE_AI_API_KEY found in environment variables!")
        
        # Initialize Google AI with the first available key
        self.google_model = None
        self._current_google_idx = 0
        
        if self.google_ai_keys and GOOGLE_AI_AVAILABLE:
            self._configure_google_key(0)
            logging.info(f"🌟 Google AI Studio loaded {len(self.google_ai_keys)} key(s). Primary key length: {len(self.google_ai_keys[0])}")
        elif not GOOGLE_AI_AVAILABLE:
            logging.warning("⚠️ google.generativeai module NOT available (ImportError)!")
        
        # Backward compat
        self.google_ai_key = self.google_ai_keys[0] if self.google_ai_keys else None
        
        if not self.api_keys and not self.google_model:
            raise ValueError("No API keys found! Need OPENROUTER_API_KEY or GOOGLE_AI_API_KEY")
        
        logging.info(f"🔑 Loaded {len(self.api_keys)} OpenRouter key(s), {len(self.google_ai_keys)} Google AI key(s)")
        
        self.current_key_index = 0
        if self.api_keys:
            self._init_client()
            self.models = self.get_best_free_models()
        else:
            self.client = None
            self.models = []

    def _init_client(self):
        """Initialize OpenAI client with current key."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_keys[self.current_key_index],
        )

    def _switch_to_backup_key(self):
        """Switch to backup key if available."""
        if self.current_key_index < len(self.api_keys) - 1:
            self.current_key_index += 1
            logging.info(f"🔄 Switching to OpenRouter backup key #{self.current_key_index + 1}")
            self._init_client()
            return True
        return False

    def _configure_google_key(self, idx: int):
        """Configure Google AI with a specific key by index."""
        try:
            genai.configure(api_key=self.google_ai_keys[idx])
            self.google_model = genai.GenerativeModel('gemini-2.0-flash')
            self._current_google_idx = idx
            logging.info(f"🔑 Google AI: Configured key #{idx + 1}/{len(self.google_ai_keys)}")
        except Exception as e:
            logging.error(f"❌ Google AI Init Failed for key #{idx + 1}: {e}")
            self.google_model = None

    def _rotate_google_key(self) -> bool:
        """Rotate to the next non-exhausted Google AI key. Returns True if a key is available."""
        global _google_exhausted_keys
        for offset in range(1, len(self.google_ai_keys)):
            idx = (self._current_google_idx + offset) % len(self.google_ai_keys)
            if idx not in _google_exhausted_keys:
                logging.info(f"🔄 Rotating to Google AI key #{idx + 1}...")
                self._configure_google_key(idx)
                return True
        logging.warning("🚫 All Google AI keys exhausted for today.")
        return False

    def _all_google_keys_exhausted(self) -> bool:
        """Check if all Google AI keys have been daily-exhausted."""
        global _google_exhausted_keys
        if not self.google_ai_keys:
            return True
        return len(_google_exhausted_keys) >= len(self.google_ai_keys)

    def _generate_with_google_ai(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate via Google AI Studio (Gemini) with pre-call rate limiting."""
        global _google_exhausted_keys, _last_google_call_ts

        if not self.google_model or self._all_google_keys_exhausted():
            return None

        # Skip if current key is exhausted (try rotation first)
        if self._current_google_idx in _google_exhausted_keys:
            if not self._rotate_google_key():
                return None

        # Enforce minimum spacing between Google AI calls
        _rate_limit_pre_call()

        logging.info(f"🌟 Trying Google AI Studio (Key #{self._current_google_idx + 1})...")
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.google_model.generate_content(full_prompt)

            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            result = json.loads(text.strip())
            logging.info("✅ Google AI Studio succeeded!")
            return result

        except Exception as e:
            err = str(e)
            logging.error(f"❌ Google AI Studio (Key #{self._current_google_idx + 1}) failed: {e}")

            # Check if this is a daily quota exhaustion → mark this key
            if "429" in err and _is_daily_quota_error(err):
                _google_exhausted_keys.add(self._current_google_idx)
                logging.warning(f"🚫 Google AI Key #{self._current_google_idx + 1} daily quota exhausted.")

            return None

    def get_best_free_models(self) -> list:
        """Fetches and ranks free models from OpenRouter."""
        try:
            logging.info("🔎 Discovering best free models on OpenRouter...")
            response = requests.get("https://openrouter.ai/api/v1/models")
            if response.status_code != 200:
                return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
            
            all_models = response.json().get("data", [])
            free_models = []
            
            for m in all_models:
                pricing = m.get("pricing", {})
                if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                    free_models.append(m["id"])
            
            scored_models = []
            for mid in free_models:
                score = 0
                mid_lower = mid.lower()
                
                if "gemini" in mid_lower: score += 10
                if "llama-3" in mid_lower: score += 8
                if "deepseek" in mid_lower: score += 7
                if "phi-4" in mid_lower: score += 6
                if "flash" in mid_lower: score += 3
                if "exp" in mid_lower: score += 2
                if "70b" in mid_lower: score += 2
                if "nano" in mid_lower or "1b" in mid_lower or "3b" in mid_lower: score -= 20
                
                scored_models.append((score, mid))
            
            scored_models.sort(key=lambda x: x[0], reverse=True)
            best_models = [m[1] for m in scored_models[:5]]
            
            logging.info(f"✅ Selected Top Free Models: {best_models}")
            models = best_models if best_models else [OPENROUTER_GEMINI_FREE]
            return self._prioritize_openrouter_gemini(models)

        except Exception as e:
            logging.error(f"⚠️ Model discovery failed: {e}")
            return [OPENROUTER_GEMINI_FREE, "meta-llama/llama-3.3-70b-instruct:free"]

    def _prioritize_openrouter_gemini(self, models: list) -> list:
        """Put OpenRouter Gemini free first when direct Google quota is exhausted."""
        ordered = list(models)
        if OPENROUTER_GEMINI_FREE in ordered:
            ordered.remove(OPENROUTER_GEMINI_FREE)
        if _should_skip_google():
            ordered.insert(0, OPENROUTER_GEMINI_FREE)
        return ordered

    def _generate_script(self, eto: str, date: str, period_type: str, system_prompt: str, user_prompt: str) -> dict:
        """Helper to try models in rotation with smart backoff and multi-key rotation."""
        global _google_exhausted_keys, _openrouter_daily_exhausted

        # ── PRIORITY 1: GOOGLE AI (all keys with rotation) ──
        if self.google_ai_keys and GOOGLE_AI_AVAILABLE and not self._all_google_keys_exhausted():
            logging.info(f"✨ Using Google AI for {period_type} ({len(self.google_ai_keys)} key(s) available)...")

            # Try each key with exponential backoff
            max_google_attempts = 5
            backoff_base = 15  # seconds

            for attempt in range(max_google_attempts):
                # If current key is exhausted, rotate
                if self._current_google_idx in _google_exhausted_keys:
                    if not self._rotate_google_key():
                        logging.warning("⚠️ All Google AI keys daily-exhausted. Falling back to OpenRouter.")
                        break

                google_result = self._generate_with_google_ai(system_prompt, user_prompt)
                if google_result:
                    logging.info(f"✅ Google AI Generation Successful! Post-call cooldown 15s...")
                    time.sleep(15)
                    return google_result

                # If current key just got daily-exhausted, immediately try rotating
                if self._current_google_idx in _google_exhausted_keys:
                    if self._rotate_google_key():
                        logging.info(f"🔄 Switched to Google AI Key #{self._current_google_idx + 1}, retrying immediately...")
                        continue  # Don't wait — try the new key right away
                    else:
                        break  # All keys exhausted

                # Per-minute rate limit — wait with exponential backoff
                wait = min(backoff_base * (2 ** attempt), 120)
                logging.warning(
                    f"⚠️ Google AI attempt {attempt + 1}/{max_google_attempts} failed. "
                    f"Waiting {wait}s (exponential backoff)..."
                )
                time.sleep(wait)

            if not self._all_google_keys_exhausted():
                logging.warning(f"⚠️ Google AI exhausted ({max_google_attempts} attempts). Falling back to OpenRouter...")
        elif self._all_google_keys_exhausted():
            logging.info(f"⏭️ Skipping Google AI for {period_type} (all keys exhausted). Using OpenRouter...")
            self.models = self._prioritize_openrouter_gemini(self.models)

        # ── PRIORITY 2: OPENROUTER (multiple models + key rotation) ──
        if _openrouter_daily_exhausted:
            logging.warning("🚫 OpenRouter daily free limit already exhausted. Skipping.")
        elif self.client:
            errors = []
            max_loop_retries = 2

            for attempt in range(max_loop_retries):
                if _openrouter_daily_exhausted:
                    break

                for model in self.models:
                    if _openrouter_daily_exhausted:
                        break

                    logging.info(f"🤖 Generating {period_type} fortune using: {model}")
                    try:
                        try:
                            response = self.client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                response_format={"type": "json_object"}
                            )
                            raw_content = response.choices[0].message.content
                        except Exception as e:
                            if "400" in str(e):
                                logging.warning(f"⚠️ Model {model} rejected JSON mode. Retrying with Plain Text...")
                                response = self.client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {"role": "system", "content": system_prompt + "\\n\\nIMPORTANT: Return ONLY valid JSON. No markdown."},
                                        {"role": "user", "content": user_prompt}
                                    ]
                                )
                                raw_content = response.choices[0].message.content
                            else:
                                raise e

                        clean_json = raw_content.replace('```json', '').replace('```', '').strip()

                        logging.info("✅ OpenRouter Generation Successful!")
                        time.sleep(3)
                        return json.loads(clean_json)

                    except Exception as e:
                        error_str = str(e)
                        logging.warning(f"⚠️ Model {model} failed: {e}")
                        errors.append(f"{model}: {error_str}")

                        # Detect daily free limit exhaustion → skip ALL OpenRouter retries
                        if "free-models-per-day" in error_str.lower() or "Remaining\': \'0\'" in error_str:
                            logging.warning("🚫 Daily free model limit reached! Skipping all OpenRouter retries.")
                            _openrouter_daily_exhausted = True
                            break

                        # Rate Limit: Try rotating API key first
                        if _is_rate_limit_error(error_str):
                            if len(self.api_keys) > 1:
                                old_idx = self.current_key_index
                                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                                if self.current_key_index != old_idx:
                                    logging.info(f"🔄 Rotating to OpenRouter key #{self.current_key_index + 1}...")
                                    self._init_client()
                                    time.sleep(5)
                                    continue

                            wait_time = max(_parse_retry_seconds(error_str), 45)
                            logging.info(
                                f"⏳ Rate Limit (429) hit. Sleeping {wait_time}s before next model..."
                            )
                            time.sleep(wait_time)
                        else:
                            time.sleep(5)

                        continue

                logging.info(f"🔄 Loop {attempt+1}/{max_loop_retries} finished. Waiting 20s before restarting...")
                time.sleep(20)

        # ── LAST RESORT: Try Google AI one final time (wait for per-minute reset) ──
        if self.google_ai_keys and GOOGLE_AI_AVAILABLE and not self._all_google_keys_exhausted():
            logging.info("🆘 Last resort: Waiting 60s then trying Google AI one final time...")
            time.sleep(60)  # Wait for per-minute quota to potentially reset
            google_result = self._generate_with_google_ai(system_prompt, user_prompt)
            if google_result:
                logging.info("✅ Google AI Last Resort succeeded!")
                time.sleep(15)
                return google_result

        raise Exception(f"❌ API Quota Exceeded. Cannot generate content for {eto}.")

    def generate_daily_fortune(self, eto: str, date: str, rokuyo: dict, season: str, eto_info: dict, deep_data: dict = None) -> dict:
        """Generates Daily Japanese Fortune (今日の運勢)."""
        logging.info(f"✨ 星野先生: Generating Daily Fortune for {eto}...")
        
        # Merge Deep Data if available
        rokuyo_info = f"{rokuyo['name']} ({rokuyo['romaji']})"
        rokuyo_meaning = rokuyo['meaning']
        
        kyusei_str = ""
        sekki_str = ""
        choku_str = ""
        
        if deep_data:
            if 'rokuyo' in deep_data and deep_data['rokuyo']:
                r = deep_data['rokuyo']
                rokuyo_info = f"{r.get('name', rokuyo['name'])} (True Lunar Rokuyo)"
                rokuyo_meaning = r.get('meaning', rokuyo_meaning)
            
            if 'kyusei' in deep_data and deep_data['kyusei']:
                k = deep_data['kyusei']
                kyusei_str = f"5. **九星 (Kyusei)**: {k.get('name')} - Element: {k.get('element')}"
                
            if 'sekki' in deep_data and deep_data['sekki']:
                sekki_str = f"6. **二十四節気 (Solar Term)**: {deep_data['sekki']}"
                
            if 'choku' in deep_data and deep_data['choku']:
                c = deep_data['choku']
                choku_str = f"7. **十二直 (Choku)**: {c.get('name')} ({c.get('meaning')})"
        
        system_prompt = f"""
You are 「星野先生」 (Hoshino-sensei), a renowned Japanese fortune teller (占い師) with 30+ years of experience.
You are trained in authentic Japanese divination systems.

You MUST use these REAL Japanese astrology systems in your predictions:

1. **干支 (Eto)**: {eto_info['kanji']}年 ({eto_info['animal']}) - Element: {eto_info['element']}
   - Personality: Based on traditional {eto_info['animal']} characteristics
   - Compatible with: {', '.join(eto_info.get('compat', []))}
   - Challenging with: {', '.join(eto_info.get('incompat', []))}

2. **六曜 (Rokuyo)**: Today is {rokuyo_info}
   - Meaning: {rokuyo_meaning}
   - Best for: {rokuyo['best']}
   - Avoid: {rokuyo['avoid']}

3. **五行 (Gogyou/Five Elements)**: {eto_info['element'].upper()} energy dominant
   - Water (水) creates Wood, controls Fire
   - Wood (木) creates Fire, controls Earth
   - Fire (火) creates Earth, controls Metal
   - Earth (土) creates Metal, controls Water
   - Metal (金) creates Water, controls Wood

4. **季節 (Season)**: {season}
{kyusei_str}
{sekki_str}
{choku_str}

CRITICAL RULES:
- Write ALL content in NATURAL JAPANESE using Kanji, Hiragana, and Katakana
- NO typos or grammatical errors in Japanese
- **AVOID TOXIC POSITIVITY**: Life has ups and downs. Be honest. If the day implies caution, say it clearly.
- **TRUTHFUL & ACCURATE**: Base every prediction strictly on the Element relationships and Deep Astrology data provided.
- **DYNAMIC & RELATABLE**: The "Hook" must sound like a real friend warning or encouraging you. Connect to daily life (work stress, relationship doubts, small joys).
- **SPECIFIC REMEDIES**: For every negative aspect, provide a CONCRETE, DOABLE remedy (action, item, or mindset).
- Use authentic fortune-telling terminology: 吉、凶、大吉、運気、開運、相性
- Lucky items must be SPECIFIC and related to the {eto_info['element']} element.

Tone: **THE VOICE OF A MASTER**. Like a wise, empathetic grandfather/grandmother speaking 1-on-1. Warm, authoritative, yet deeply personal. **ABSOLUTELY NO ROBOTIC OR GENERIC PHRASING**.
"""
        
        user_prompt = f"""
Generate a **Daily Fortune (今日の運勢)** for **{eto}** ({eto_info['kanji']}年) for **{date}**.

The fortune should reflect today's {rokuyo_info} energy and give specific, actionable advice.

Return ONLY valid JSON with this structure:
{{
    "hook": "Attention-grabbing opening (Japanese, 1-2 sentences). MUST BE RELATABLE. Example: 'You might feel a sudden disconnect today...' or 'A surprise chance awaits...'",
    "cosmic_context": "Today's {rokuyo_info} influence + Element interaction (Japanese)",
    "love": "恋愛運 - Love fortune. Be balanced. If bad, say why. (Japanese)",
    "career": "仕事運 - Work/career fortune. Include potential pitfalls. (Japanese)",
    "money": "金運 - Financial fortune. Specific advice, not just 'good luck'. (Japanese)",
    "health": "健康運 - Health fortune. Seasonal + Element based. (Japanese)",
    "remedy": "開運の鍵 (REMEDY) - Specific actionable remedy for today's challenges. NOT generic. (Japanese)",
    "lucky_item": "Specific item related to today's element (Japanese)",
    "lucky_color": "Color in Japanese (e.g., 赤、青、金)",
    "lucky_direction": "Direction in Japanese (e.g., 東、南東)",
    "lucky_number": "Number with brief meaning",
    "caution": "What to be careful about today (Japanese). Be sharp and accurate.",
    "metadata": {{
        "title": "Viral YouTube Shorts title - MUST include what video is about + {eto_info['kanji']}年 + emoji + #shorts (max 80 chars)",
        "description": "EXTREMELY DETAILED, VIRAL Description (2000+ chars). Summarize the fortune, include the hook, advice, and a call to action. FILL THE SPACE. Use these tags: {self._get_trending_tags()}. MUST include the 2026 Zodiac Guide.",
        "tags": ["shorts", "占い", "今日の運勢", "干支占い", "{eto_info['kanji']}年", "運勢", "スピリチュアル", "開運", "{rokuyo_info}", "恋愛運", "金運", "仕事運", "fyp", "viral", "2026年運勢"]
    }}
}}
"""
        script = self._generate_script(eto, date, "Daily", system_prompt, user_prompt)
        # Post-process to ensure Zodiac Guide is present
        if script and "metadata" in script:
            desc = script["metadata"].get("description", "")
            if "【自分の干支の調べ方】" not in desc and "【⚠️自分の干支がわからない方へ⚠️】" not in desc:
                script["metadata"]["description"] = desc + "\\n\\n" + self._get_zodiac_guide()
        return script

    def generate_monthly_fortune(self, eto: str, month_year: str, eto_info: dict) -> dict:
        """Generates Monthly Fortune (月間運勢)."""
        logging.info(f"✨ 星野先生: Generating Monthly Fortune for {eto} ({month_year})...")
        
        system_prompt = f"""
You are 「星野先生」 (Hoshino-sensei), a renowned Japanese fortune teller.
You specialize in monthly predictions using 九星気学 (Kyusei Kigaku/Nine Star Ki).

For {eto_info['kanji']}年 ({eto_info['animal']}):
- Element: {eto_info['element']}
- This month focuses on the flow of 気 (Ki/energy) throughout the month

CRITICAL: Write ALL content in NATURAL JAPANESE with NO typos.
Use formal but warm Japanese suitable for fortune-telling.
**DO NOT SUGARCOAT**. If the stars say struggle, predict struggle, but provide a **remedy**.
"""
        
        user_prompt = f"""
Generate a **Monthly Fortune (月間運勢)** for **{eto}** ({eto_info['kanji']}年) for **{month_year}**.

Return ONLY valid JSON:
{{
    "hook": "Compelling monthly theme hook (Japanese). Honest and Real.",
    "cosmic_context": "This month's energy overview (Japanese). Based on Kyusei Kigaku.",
    "love": "恋愛運 - Monthly love forecast. Specific highs and lows. (Japanese)",
    "career": "仕事運 - Monthly career forecast. Specific challenges and wins. (Japanese)",
    "money": "金運 - Monthly financial forecast. Real advice. (Japanese)",
    "health": "健康運 - Monthly health focus. (Japanese)",
    "remedy": "今月の開運対策 (Monthly Remedy) - Actionable advice for the month's hardest challenge. (Japanese)",
    "lucky_dates": "Best dates this month (list in Japanese)",
    "caution_dates": "Challenging dates to be careful (Japanese)",
    "monthly_advice": "Overall advice for the month (Japanese)",
    "lucky_item": "Monthly power item (Japanese)",
    "lucky_color": "Monthly lucky color (Japanese)",
    "metadata": {{
        "title": "Monthly title with 月間運勢 + {eto_info['kanji']}年 + {month_year} + emoji + #shorts",
        "description": "DETAILED Monthly Description (2000+ chars). Deep dive into this month's fate. Use these tags: {self._get_trending_tags()}. MUST include the 2026 Zodiac Guide.",
        "tags": ["shorts", "月間運勢", "占い", "{eto_info['kanji']}年", "運勢", "スピリチュアル", "2026年運勢"]
    }}
}}
"""
        script = self._generate_script(eto, month_year, "Monthly", system_prompt, user_prompt)
        # Post-process to ensure Zodiac Guide is present
        if script and "metadata" in script:
            desc = script["metadata"].get("description", "")
            if "【自分の干支の調べ方】" not in desc and "【⚠️自分の干支がわからない方へ⚠️】" not in desc:
                script["metadata"]["description"] = desc + "\\n\\n" + self._get_zodiac_guide()
        return script

    def generate_yearly_fortune(self, eto: str, year: str, eto_info: dict) -> dict:
        """Generates Yearly Fortune (年間運勢)."""
        logging.info(f"✨ 星野先生: Generating Yearly Fortune for {eto} ({year})...")
        
        system_prompt = f"""
You are 「星野先生」 (Hoshino-sensei), Japan's most respected fortune teller.
You are making the GRAND YEARLY PREDICTION for {year}年.

For {eto_info['kanji']}年 ({eto_info['animal']}):
- Element: {eto_info['element']}
- Focus on major life themes, transformations, and opportunities

Use a grand, prophetic tone while remaining warm and encouraging.
CRITICAL: Write ALL content in NATURAL JAPANESE with NO typos.
"""
        
        user_prompt = f"""
Generate a **Yearly Fortune (年間運勢)** for **{eto}** ({eto_info['kanji']}年) for **{year}年**.

Return ONLY valid JSON:
{{
    "hook": "Grand yearly theme revelation (Japanese, impactful). Honest and Powerful.",
    "cosmic_context": "{year}年's cosmic energy for {eto_info['kanji']}年 (Japanese)",
    "love": "恋愛運 - Year's love destiny. Real highs/lows. (Japanese)",
    "career": "仕事運 - Year's career trajectory. Challenges & Success. (Japanese)",
    "money": "金運 - Year's wealth potential. Realistic advice. (Japanese)",
    "health": "健康運 - Year's health focus. (Japanese)",
    "remedy": "年間開運の鍵 (Yearly Remedy) - The single most important action to survive/thrive this year. (Japanese)",
    "lucky_months": "Best months of the year (Japanese)",
    "challenge_months": "Months requiring caution (Japanese)",
    "yearly_theme": "The single most important theme for {year} (Japanese)",
    "power_word": "Your power word for {year} (Japanese kanji with meaning)",
    "metadata": {{
        "title": "Yearly title with 年間運勢 + {year}年 + {eto_info['kanji']}年 + grand emoji + #shorts",
        "description": "LEGENDARY Yearly Description (3000+ chars). Predict the entire year in detail. Use these tags: {self._get_trending_tags()}. MUST include the 2026 Zodiac Guide.",
        "tags": ["shorts", "年間運勢", "{year}年運勢", "占い", "{eto_info['kanji']}年", "2026年運勢"]
    }}
}}
"""
        script = self._generate_script(eto, year, "Yearly", system_prompt, user_prompt)
        # Post-process to ensure Zodiac Guide is present
        if script and "metadata" in script:
            desc = script["metadata"].get("description", "")
            if "【自分の干支の調べ方】" not in desc and "【⚠️自分の干支がわからない方へ⚠️】" not in desc:
                script["metadata"]["description"] = desc + "\\n\\n" + self._get_zodiac_guide()
        return script

    def generate_daily_advice(self, eto: str, date: str, rokuyo: dict, eto_info: dict) -> dict:
        """Generates Daily Advice/Remedy (開運アドバイス)."""
        logging.info(f"✨ 星野先生: Generating Daily Advice for {eto}...")
        
        system_prompt = f"""
You are 「星野先生」 (Hoshino-sensei), specializing in 開運 (fortune improvement) advice.

Today is {rokuyo['name']} ({rokuyo['romaji']}): {rokuyo['meaning']}

For {eto_info['kanji']}年 ({eto_info['animal']}):
Provide specific, actionable advice to improve fortune today.

CRITICAL: Write ALL content in NATURAL JAPANESE with NO typos.
"""
        
        user_prompt = f"""
Generate **Daily Advice (開運アドバイス)** for **{eto}** ({eto_info['kanji']}年) for **{date}**.

Focus on ONE specific problem and provide detailed solution.

Return ONLY valid JSON:
{{
    "hook": "Emotional hook about today's challenge (Japanese)",
    "problem": "What {eto_info['kanji']}年 people might face today (Japanese)",
    "solution": "Step-by-step advice to overcome it (Japanese)",
    "morning_ritual": "Morning practice for good luck (Japanese)",
    "evening_ritual": "Evening practice for balance (Japanese)",
    "power_phrase": "Phrase to repeat today (Japanese)",
    "avoid": "What to definitely avoid today (Japanese)",
    "lucky_item": "Item that helps today (Japanese)",
    "lucky_color": "Color that helps today (Japanese)",
    "metadata": {{
        "title": "Advice title with 開運 + specific topic + {eto_info['kanji']}年 + #shorts",
        "description": "DETAILED Advice Description (2000+ chars). Explain the ritual and advice in depth. Use these tags: {self._get_trending_tags()}. MUST include the 2026 Zodiac Guide.",
        "tags": ["shorts", "開運", "アドバイス", "占い", "{eto_info['kanji']}年", "2026年運勢"]
    }}
}}
"""
        script = self._generate_script(eto, date, "Daily_Advice", system_prompt, user_prompt)
        # Post-process to ensure Zodiac Guide is present
        if script and "metadata" in script:
            desc = script["metadata"].get("description", "")
            if "【自分の干支の調べ方】" not in desc and "【⚠️自分の干支がわからない方へ⚠️】" not in desc:
                script["metadata"]["description"] = desc + "\\n\\n" + self._get_zodiac_guide()
        return script

    def generate_viral_metadata(self, eto: str, date_str: str, period_type: str, script_data, eto_info: dict) -> dict:
        """Generates Viral YouTube Metadata dynamically."""
        logging.info(f"🚀 星野先生: Generating Viral Metadata for {eto} ({period_type})...")
        
        if isinstance(script_data, list):
            script_data = script_data[0] if script_data else {}
        
        context = ""
        if isinstance(script_data, dict):
            context = f"Hook: {script_data.get('hook', '')}. Theme: {script_data.get('cosmic_context', '')}"
        
        system_prompt = """
You are a YouTube Shorts viral content strategist for Japanese fortune-telling (占い).

Your goal: Create IRRESISTIBLE, CLICKABLE metadata that gets views.

TITLE RULES (CRITICAL):
1. Start with attention emoji (🔥⚠️💰💕✨🌟😱)
2. Describe WHAT THIS VIDEO reveals (not generic)
3. Include Eto name in Japanese (子年, 丑年, etc.)
4. MUST end with #shorts
5. Max 80 characters
6. Use curiosity gaps: "〇〇年さん注意！", "〇〇年に大ニュース！"

DESCRIPTION RULES:
1. MAXIMIZE LENGTH (target 3000-5000 characters). 
2. STRUCTURE:
   - 🔥 Catchy Hook (First 2 sentences are crucial)
   - ⚠️ Important Warning or Key Prediction
   - 📜 Full Detailed Reading (Love, Work, Money) - Expand on the video content. Write A LOT here.
   - 💡 Actionable Advice & Rituals
   - 🍀 Lucky Items/Colors List
   - 📣 Call to Subscribe & Comment
   - 🏷️ Hashtag Block (30+ tags)
   - 🐁 Zodiac Finder Guide (at the very bottom)
3. Use lots of relevant emojis.
4. NO TYPOS in Japanese text.
"""
        
        viral_tags = self._get_trending_tags()
        zodiac_guide = self._get_zodiac_guide()

        user_prompt = f"""
Generate YouTube Metadata for a **{period_type}** fortune video.
**Eto**: {eto} ({eto_info['kanji']}年)
**Date**: {date_str}
**Content Highlight**: {context}

Return ONLY valid JSON:
{{
    "title": "Viral title (Japanese + emoji, MUST end with #shorts, max 80 chars)",
    "description": "EXTREMELY LONG, VIRAL DESCRIPTION (3000-5000 chars). Use these tags: {viral_tags}. \n\nCONTENT MUST INCLUDE THIS GUIDE AT THE BOTTOM:\n{zodiac_guide}",
    "tags": ["shorts", "占い", "今日の運勢", "干支占い", "{eto_info['kanji']}年", "運勢", "スピリチュアル", "2026年運勢", ...]
}}
"""
        
        result = self._generate_script(eto, date_str, f"Metadata_{period_type}", system_prompt, user_prompt)
        
        if isinstance(result, list):
            result = result[0] if result else {}
        
        if not isinstance(result, dict) or 'title' not in result:
             # Fallback logic if AI fails
             return {
                 "title": f"🔮 {eto_info['kanji']}年の運勢 {date_str} #shorts",
                 "description": f"今日の運勢です！\\n\\n{zodiac_guide}\\n\\n{viral_tags}",
                 "tags": ["shorts", "占い"]
             }

        # Ensure #shorts is in title
        title = result.get('title', '')
        if '#shorts' not in title.lower():
            if len(title) > 70:
                title = title[:67] + "..."
            title = title.rstrip() + " #shorts"
        result['title'] = title
        
        # Ensure description has guide
        desc = result.get('description', '')
        if "【自分の干支の調べ方】" not in desc and "【⚠️自分の干支がわからない方へ⚠️】" not in desc:
             result['description'] = desc + "\\n\\n" + zodiac_guide

        if 'categoryId' not in result:
            result['categoryId'] = '24'
            
        return result
