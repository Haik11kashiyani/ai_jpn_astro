import os
import json
import logging
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

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

    def derive_daily_parameters(self, date_str: str) -> dict:
        """
        Uses LLM to derive 100% ACCURATE traditional parameters (Rokuyo, Kyusei, Solar Term).
        Replaces simple arithmetic approximations with 'Deep Astrology' knowledge.
        """
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
             # Use a quick model for data retrieval if possible, otherwise standard
            return self._generate_script("System", date_str, "Deep_Data", system_prompt, user_prompt)
        except Exception as e:
            logging.warning(f"⚠️ Deep Astrology Data failed: {e}. Falling back to standard calc.")
            return None

    def __init__(self, api_key: str = None, backup_key: str = None):
        """Initialize with OpenRouter API Keys (primary + backup) + Google AI fallback."""
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
        
        self.google_ai_key = os.getenv("GOOGLE_AI_API_KEY")
        if self.google_ai_key and GOOGLE_AI_AVAILABLE:
            genai.configure(api_key=self.google_ai_key)
            self.google_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logging.info("🌟 Google AI Studio (Gemini) fallback enabled")
        else:
            self.google_model = None
        
        if not self.api_keys and not self.google_model:
            raise ValueError("No API keys found! Need OPENROUTER_API_KEY or GOOGLE_AI_API_KEY")
        
        logging.info(f"🔑 Loaded {len(self.api_keys)} OpenRouter key(s)")
        
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
            logging.info(f"🔄 Switching to backup key #{self.current_key_index + 1}")
            self._init_client()
            return True
        return False

    def _generate_with_google_ai(self, system_prompt: str, user_prompt: str) -> dict:
        """Fallback to Google AI Studio (Gemini) when OpenRouter fails."""
        if not self.google_model:
            return None
            
        logging.info("🌟 Trying Google AI Studio (Gemini) as fallback...")
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
            logging.error(f"❌ Google AI Studio failed: {e}")
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
            return best_models if best_models else ["google/gemini-2.0-flash-exp:free"]
            
        except Exception as e:
            logging.error(f"⚠️ Model discovery failed: {e}")
            return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]

    def _generate_script(self, eto: str, date: str, period_type: str, system_prompt: str, user_prompt: str) -> dict:
        """Helper to try models in rotation with smart backoff on rate limits."""
        import time
        
        # --- PRIORITY 1: GOOGLE AI (Unlimited/Free Tier) ---
        if self.google_model:
            logging.info(f"✨ Using Google AI (Primary) for {period_type}...")
            google_result = self._generate_with_google_ai(system_prompt, user_prompt)
            if google_result:
                logging.info("✅ Google AI Generation Successful! Sleeping 5s to respect rate limits...")
                time.sleep(5) # Rate limit protection
                return google_result
            else:
                logging.warning("⚠️ Google AI Primary failed. Falling back to OpenRouter...")

        errors = []
        
        # Max retries per model type
        max_loop_retries = 3 
        
        for attempt in range(max_loop_retries):
            for model in self.models:
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
                    time.sleep(2) # Small break for OpenRouter
                    return json.loads(clean_json)
                    
                except Exception as e:
                    error_str = str(e)
                    logging.warning(f"⚠️ Model {model} failed: {e}")
                    errors.append(f"{model}: {error_str}")
                    
                    # Smart Backoff for Rate Limits
                    if "429" in error_str or "rate limit" in error_str.lower():
                        if "free" in model:
                            wait_time = 180 # 3 mins for free models
                        else:
                            wait_time = 60  # 1 min for others
                            
                        logging.info(f"⏳ Rate Limit (429) hit. Sleeping {wait_time}s before next retry...")
                        time.sleep(wait_time)
                    else:
                        # Non-rate limit error (e.g. 500, overload)
                        time.sleep(5)
                    
                    continue # Try next model
            
            logging.info(f"🔄 Loop {attempt+1}/{max_loop_retries} finished. Waiting 30s before restarting model loop...")
            time.sleep(30)
        
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
- **DYNAMIC & RELATABLE**: The "Hook" must sound like a real friend warning or encouraging you. Connect to daily life.
- **SPECIFIC REMEDIES**: For every negative aspect, provide a CONCRETE, DOABLE remedy.
- Use authentic fortune-telling terminology: 吉、凶、大吉、運気、開運、相性
- Lucky items must be SPECIFIC and related to the {eto_info['element']} element.

Tone: Mystical but grounded, honest, empathetic, and 100% authentic.
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
        "description": "Engaging description with 15-20 hashtags including #shorts #占い #今日の運勢 #干支占い",
        "tags": ["shorts", "占い", "今日の運勢", "干支占い", "{eto_info['kanji']}年", "運勢", "スピリチュアル", "開運", "{rokuyo_info}", "恋愛運", "金運", "仕事運"]
    }}
}}
"""
        return self._generate_script(eto, date, "Daily", system_prompt, user_prompt)

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
        "description": "Monthly description with hashtags",
        "tags": ["shorts", "月間運勢", "占い", "{eto_info['kanji']}年", "運勢", "スピリチュアル"]
    }}
}}
"""
        return self._generate_script(eto, month_year, "Monthly", system_prompt, user_prompt)

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
        "description": "Yearly description with hashtags",
        "tags": ["shorts", "年間運勢", "{year}年運勢", "占い", "{eto_info['kanji']}年"]
    }}
}}
"""
        return self._generate_script(eto, year, "Yearly", system_prompt, user_prompt)

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
        "description": "Advice description with hashtags",
        "tags": ["shorts", "開運", "アドバイス", "占い", "{eto_info['kanji']}年"]
    }}
}}
"""
        return self._generate_script(eto, date, "Daily_Advice", system_prompt, user_prompt)

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
1. First line = Curiosity hook
2. Include fortune categories covered
3. End with 15-20 viral hashtags
4. Always include: #shorts #占い #今日の運勢 #干支占い

NO TYPOS in Japanese text.
"""
        
        user_prompt = f"""
Generate YouTube Metadata for a **{period_type}** fortune video.
**Eto**: {eto} ({eto_info['kanji']}年)
**Date**: {date_str}
**Content Highlight**: {context}

Return ONLY valid JSON:
{{
    "title": "Viral title (Japanese + emoji, MUST end with #shorts, max 80 chars)",
    "description": "Engaging description ending with 15-20 hashtags",
    "tags": ["shorts", "占い", "今日の運勢", "干支占い", "{eto_info['kanji']}年", "運勢", ...]
}}
"""
        
        result = self._generate_script(eto, date_str, f"Metadata_{period_type}", system_prompt, user_prompt)
        
        if isinstance(result, list):
            result = result[0] if result else {}
        
        if not isinstance(result, dict) or 'title' not in result:
            raise Exception("Invalid metadata generated.")
        
        # Ensure #shorts is in title
        title = result.get('title', '')
        if '#shorts' not in title.lower():
            if len(title) > 70:
                title = title[:67] + "..."
            title = title.rstrip() + " #shorts"
        result['title'] = title
        
        if 'categoryId' not in result:
            result['categoryId'] = '24'
            
        return result
