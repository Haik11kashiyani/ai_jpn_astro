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
    The Astrologer Agent uses LLMs to generate authentic Vedic Astrology content.
    It acts like a knowledgeable Shastri (Astrologer).
    Supports multiple API keys with automatic failover on rate limits.
    Falls back to Google AI Studio (Gemini) when OpenRouter is exhausted.
    """
    
    def __init__(self, api_key: str = None, backup_key: str = None):
        """Initialize with OpenRouter API Keys (primary + backup) + Google AI fallback."""
        self.api_keys = []
        
        # Primary key
        primary = api_key or os.getenv("OPENROUTER_API_KEY")
        if primary:
            self.api_keys.append(primary)
        
        # Backup key
        backup = backup_key or os.getenv("OPENROUTER_API_KEY_BACKUP")
        if backup:
            self.api_keys.append(backup)
        
        # Google AI key (fallback)
        self.google_ai_key = os.getenv("GOOGLE_AI_API_KEY") or "AIzaSyDw8nEeFSWIajWJIL43u8Dt7UT5jJS_FuA"
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
            
            # Extract JSON from response
            text = response.text
            # Clean up markdown code blocks if present
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
        """
        Fetches available models from OpenRouter, filters for free ones,
        and ranks them based on heuristics (e.g. 'gemini', 'llama', '70b').
        """
        try:
            logging.info("🔎 Discovering best free models on OpenRouter...")
            response = requests.get("https://openrouter.ai/api/v1/models")
            if response.status_code != 200:
                logging.warning("⚠️ Failed to fetch models list. Using defaults.")
                return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
            
            all_models = response.json().get("data", [])
            free_models = []
            
            for m in all_models:
                pricing = m.get("pricing", {})
                if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                    free_models.append(m["id"])
            
            # Smart Ranking Heuristics
            # 1. Prefer 'gemini' (best for creative writing)
            # 2. Prefer 'llama-3' (strong instruction following)
            # 3. Prefer 'deepseek' (good reasoning)
            # 4. Prefer larger models ('70b', 'flash')
            # 5. Avoid tiny models ('nano', '1b', '3b')
            
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
            
            # Sort by score desc
            scored_models.sort(key=lambda x: x[0], reverse=True)
            
            best_models = [m[1] for m in scored_models[:5]] # Take top 5
            
            logging.info(f"✅ Selected Top Free Models: {best_models}")
            if not best_models:
                 return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
                 
            return best_models
            
        except Exception as e:
            logging.error(f"⚠️ Model discovery failed: {e}")
            # Fallback hardcoded list
            return ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]

    def _generate_script(self, rashi: str, date: str, period_type: str, system_prompt: str, user_prompt: str) -> dict:
        """Helper to try models in rotation with key failover on rate limits."""
        errors = []
        tried_backup = False
        
        while True:
            for model in self.models:
                logging.info(f"🤖 Casting {period_type} chart using: {model}")
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
                    return json.loads(raw_content)
                    
                except Exception as e:
                    error_str = str(e)
                    logging.warning(f"⚠️ Model {model} failed: {e}")
                    errors.append(f"{model}: {error_str}")
                    
                    # Check if it's a rate limit error (429)
                    if "429" in error_str or "rate limit" in error_str.lower():
                        # Try switching to backup key
                        if not tried_backup and self._switch_to_backup_key():
                            logging.info("🔄 Rate limit hit! Retrying with backup key...")
                            tried_backup = True
                            errors = []  # Reset errors for new key
                            break  # Restart model loop with new key
                    continue
            else:
                # All models exhausted for current key
                break
        
        # FINAL FALLBACK: Try Google AI Studio
        logging.warning("⚠️ All OpenRouter models/keys exhausted. Trying Google AI fallback...")
        google_result = self._generate_with_google_ai(system_prompt, user_prompt)
        if google_result:
            return google_result
        
        # CRITICAL: Do not use Mock Data for Production runs, as it ruins the channel.
        raise Exception(f"❌ API Quota Exceeded for ALL keys. Cannot generate valid content for {rashi}.")
        # return self._get_mock_data(rashi, period_type)

    def _get_mock_data(self, rashi, period_type):
        """Returns safe, pre-written content to allow testing when APIs are down."""
        logging.warning(f"⚠️ RETURNING MOCK DATA FOR {rashi} ({period_type})")
        
        # Handle Metadata mock data (for YouTube uploads)
        if period_type.startswith("Metadata_"):
            # Extract the actual period type (e.g., "Metadata_Daily" -> "Daily")
            actual_period = period_type.replace("Metadata_", "")
            today_str = datetime.now().strftime("%d %B %Y")
            
            # Extract clean rashi name for title
            clean_rashi = rashi.split('(')[0].strip() if '(' in rashi else rashi
            
            return {
                "title": f"{clean_rashi} Rashifal {today_str} | आज का राशिफल 🔮 #shorts #viral",
                "description": f"""🔮 {rashi} {actual_period} Rashifal - {today_str}

आज का राशिफल देखें और जानें कि सितारे आपके लिए क्या कहते हैं!

🌟 Topics Covered:
- प्रेम और रिश्ते
- करियर और व्यापार  
- धन और वित्त
- स्वास्थ्य

#shorts #viral #rashifal #astrology #horoscope #jyotish #{clean_rashi.lower()} #dailyhoroscope #trending""",
                "tags": [
                    f"{clean_rashi.lower()} rashifal",
                    "rashifal",
                    "horoscope",
                    "astrology",
                    "shorts",
                    "viral",
                    "jyotish",
                    "daily horoscope",
                    "aaj ka rashifal",
                    "zodiac",
                    "trending"
                ],
                "categoryId": "24"
            }
        
        if period_type == "Daily":
            return {
                "hook": f"{rashi} वालों, आज किस्मत का सितारा चमकेगा या बादलों में छिपेगा? {rashi} आज का राशिफल!",
                "intro": "आज चंद्रमा की स्थिति आपके लिए नए अवसर ला रही है। ग्रहीय गोचर आपके पक्ष में संकेत दे रहे हैं।",
                "love": "प्रेम संबंधों में आज मिठास बनी रहेगी। पुराने मतभेद सुलझने के आसार हैं।",
                "career": "कार्यक्षेत्र में आपको नई जिम्मेदारियां मिल सकती हैं। सहकर्मियों का पूरा सहयोग मिलेगा।",
                "money": "आर्थिक स्थिति सामान्य रहेगी। फिजूलखर्ची से बचें और निवेश सोच-समझकर करें।",
                "health": "सेहत का ध्यान रखें, खासकर बदलते मौसम में। योग और ध्यान से लाभ होगा।",
                "remedy": "आज हनुमान चालीसा का पाठ करें और लाल वस्तु का दान करें।",
                "lucky_color": "लाल (Red)",
                "lucky_number": "9"
            }
        return {
            "hook": "Mock Data generated due to API Rate Limits.",
            "intro": "Systems are currently offline, please check API quotas.",
            "love": "Unavailable.", "career": "Unavailable.", "money": "Unavailable.",
            "health": "Unavailable.", "remedy": "Check logs.", "lucky_date": "N/A"
        }

    def generate_daily_rashifal(self, rashi: str, date: str) -> dict:
        """Generates Daily Horoscope."""
        logging.info(f"✨ Astrologer: Generating Daily Horoscope for {rashi}...")
        
        system_prompt = """
        You are 'Rishiraj', an expert Vedic Astrologer. Tone: Mystical, Positive, Authoritative.
        Write a DAILY Horoscope Script in PURE HINDI.
        Do NOT mention specific dates.
        """
        
        user_prompt = f"""
        Generate a **Daily Horoscope** for **{rashi}** for {date}.
        Return ONLY valid JSON:
        {{
            "hook": "Short attention grabber (Hindi)",
            "intro": "Astrological context (Gochar)",
            "love": "Love prediction",
            "career": "Career prediction",
            "money": "Financial prediction",
            "health": "Health prediction",
            "remedy": "Specific Vedic remedy",
            "lucky_color": "Color",
            "lucky_number": "Number"
        }}
        """
        return self._generate_script(rashi, date, "Daily", system_prompt, user_prompt)

    def generate_monthly_forecast(self, rashi: str, month_year: str) -> dict:
        """Generates Monthly Horoscope (Detailed)."""
        logging.info(f"✨ Astrologer: Generating Monthly Horoscope for {rashi} ({month_year})...")
        
        system_prompt = """
        You are 'Rishiraj', an expert Vedic Astrologer. Tone: Detailed, Predictive, Guiding.
        Write a MONTHLY Horoscope Script in PURE HINDI.
        Focus on major planetary shifts (Sun transit, Moon phases).
        """
        
        user_prompt = f"""
        Generate a **Monthly Horoscope** for **{rashi}** for **{month_year}**.
        Return ONLY valid JSON:
        {{
            "hook": "Major theme of the month (Hindi)",
            "intro": "Overview of the month & planetary changes",
            "love": "Detailed Relationship forecast",
            "career": "Detailed Career & Business forecast",
            "money": "Financial opportunities & risks",
            "health": "Health warnings",
            "remedy": "Major monthly remedy (Upay)",
            "lucky_dates": "List of lucky dates"
        }}
        """
        return self._generate_script(rashi, month_year, "Monthly", system_prompt, user_prompt)

    def generate_yearly_forecast(self, rashi: str, year: str) -> dict:
        """Generates Yearly 2025+ Horoscope (Grand)."""
        logging.info(f"✨ Astrologer: Generating Yearly Horoscope for {rashi} ({year})...")
        
        system_prompt = """
        You are 'Rishiraj', the Grand Vedic Astrologer. Tone: Epic, Visionary, Comprehensive.
        Write a YEARLY 'Varshiphal' Script in PURE HINDI.
        Focus on Jupiter (Guru), Saturn (Shani), and Rahu/Ketu transits.
        """
        
        user_prompt = f"""
        Generate a **Yearly Horoscope** for **{rashi}** for the year **{year}**.
        Return ONLY valid JSON:
        {{
            "hook": "The biggest theme of the year (Hindi)",
            "intro": "Grand overview of {year} for this sign",
            "love": "Love life analysis for the whole year",
            "career": "Career growth analysis",
            "money": "Wealth accumulation forecast",
            "health": "Major health periods to watch",
            "remedy": "Maha-Upay (Grand Remedy) for the year",
            "lucky_months": "Best months of the year"
        }}
        """
        return self._generate_script(rashi, year, "Yearly", system_prompt, user_prompt)

    def generate_daily_remedy_script(self, rashi: str, date: str) -> dict:
        """Generates a detailed Daily Remedy (Upay) deep-dive script (Evening Content)."""
        logging.info(f"✨ Astrologer: Generating Daily Remedy Deep Dive for {rashi}...")
        
        system_prompt = """
        You are 'Acharya Rishiraj', an expert in Vedic Remedies (Lal Kitab & Puranic).
        Tone: Empathetic, Spiritual, Problem-Solving.
        Write a DETAILED, 2-minute script focusing ONLY on a specific remedy for the day.
        Structure it like a spiritual counseling session.
        """
        
        user_prompt = f"""
        Generate a **Daily Remedy Deep Dive** for **{rashi}** for **{date}**.
        Focus on ONE major problem people of this sign might face today (based on planetary transit) and provide a powerful, detailed remedy.
        
        Return ONLY valid JSON:
        {{
            "hook": "Emotional hook addressing the problem (Hindi)",
            "intro": "Explain WHY this problem is happening today (Planetary Context)",
            "remedy_detailed": "Step-by-step detailed remedy instructions",
            "mantra": "A specific mantra to chant",
            "caution": "What NOT to do today",
            "motivation": "Closing spiritual motivation"
        }}
        """
        return self._generate_script(rashi, date, "Daily_Remedy", system_prompt, user_prompt)

    def generate_viral_metadata(self, rashi: str, date_str: str, period_type: str, script_data) -> dict:
        """
        Generates Viral YouTube Metadata (Title, Desc, Tags) using the LLM.
        This provides fully dynamic, content-aware metadata instead of static templates.
        """
        logging.info(f"🚀 Astrologer: Generating Viral Metadata for {rashi} ({period_type})...")
        
        # Handle script_data being a list (unwrap single-item lists)
        if isinstance(script_data, list):
            if len(script_data) > 0 and isinstance(script_data[0], dict):
                script_data = script_data[0]
            else:
                script_data = {}
        
        # Safely extract context
        if isinstance(script_data, dict):
            context = f"Hook: {script_data.get('hook', '')}. Theme: {script_data.get('intro', '')}"
        else:
            context = "Daily horoscope prediction"
        
        system_prompt = """
        You are a YouTube Growth Hacker & Viral Content Strategist.
        Your goal is to WRITE HIGH-CTR, SEO-OPTIMIZED METADATA.
        
        RULES FOR TITLES:
        1. **CLEAN & SHOCKING**: Use punchy Hindi/English mix. "Mesh Rashifal: BIG NEWS"
        2. **MINIMAL EMOJIS**: Use MAX 1 emoji at the very end. Do NOT spam emojis in the title.
        3. **NO CLICKBAIT SPAM**: Avoid "😱😱😱". Use words like "सच्चाई" (Truth), "चमत्कार" (Miracle), "सावधान" (Beware).
        
        RULES FOR DESCRIPTION & TAGS:
        1. **DYNAMIC HASHTAGS**: Generate hashtags based on the specific prediction (e.g., #money, #love, #shani).
        2. **TRENDING TAGS**: ALWAYS include these high-volume tags: #astrology #rashifal #horoscope #jyotish #zodiac #dailyhoroscope #shorts #viral
        3. **MAXIMIZE TAGS**: Fill the description with 15-20 relevant hashtags mixed with keywords.
        """
        
        # Current Trending Keywords for 2026/Astro
        trending_keywords = "2026, Saturn Transit, Shani Gochar, Guru Gochar, Rahu Ketu, Love Life, Money Healing"
        
        user_prompt = f"""
        Generate YouTube Metadata for a **{period_type}** video.
        **Rashi**: {rashi}
        **Date**: {date_str}
        **Content Highlight**: {context}
        **Trending Context**: {trending_keywords}
        
        Return ONLY valid JSON:
        {{
            "title": "Creative, Punchy Title (Max 80 chars). {rashi} {date_str}. Ends with 1 relevant emoji.",
            "description": "Engaging summary in Hindi/English. Must include sections: '✨ Prediction', '🌟 Lucky Number/Color'. END with a block of 20+ viral hashtags (Dynamic + Trending).",
            "tags": ["List of 25+ high-volume tags. Mix broad (#astrology) and specific (#{rashi.lower()}rashifal)"]
        }}
        """
        
        # Generate and validate
        result = self._generate_script(rashi, date_str, f"Metadata_{period_type}", system_prompt, user_prompt)
        
        # Handle list result (unwrap if needed)
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                result = result[0]
            else:
                # Fail hard on metadata too
                raise Exception(f"Metadata generation failed (Quota). Stopping upload for {rashi}.")
        
        # Validate required keys exist
        if not isinstance(result, dict) or 'title' not in result:
            logging.warning("⚠️ Invalid metadata result.")
            raise Exception("Invalid metadata generated.")
        
        # Ensure categoryId exists
        if 'categoryId' not in result:
            result['categoryId'] = '24'
            
        return result

# Test Run (Uncomment to test)
# if __name__ == "__main__":
#     agent = AstrologerAgent()
#     print(json.dumps(agent.generate_daily_rashifal("Kumbh (Aquarius)", "2024-12-21"), indent=2, ensure_ascii=False))
