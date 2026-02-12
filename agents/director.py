import os
import json
import logging
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Try to import Google AI
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DirectorAgent:
    """
    The Director Agent converts a Japanese fortune script into a Visual Screenplay.
    Focuses on authentic Japanese aesthetics: cherry blossoms, temples, zen gardens.
    """
    
    def __init__(self, api_key: str = None, backup_key: str = None):
        """Initialize with OpenRouter API Keys + Google AI fallback."""
        self.api_keys = []
        
        primary = api_key or os.getenv("OPENROUTER_API_KEY")
        if primary:
            self.api_keys.append(primary)
        
        backup = backup_key or os.getenv("OPENROUTER_API_KEY_BACKUP")
        if backup:
            self.api_keys.append(backup)
        
        self.google_ai_key = os.getenv("GOOGLE_AI_API_KEY")
        if self.google_ai_key and GOOGLE_AI_AVAILABLE:
            genai.configure(api_key=self.google_ai_key)
            self.google_model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.google_model = None
        
        if not self.api_keys and not self.google_model:
            raise ValueError("No API keys found!")
        
        self.current_key_index = 0
        if self.api_keys:
            self._init_client()
            self.models = self._get_best_free_models()
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
            logging.info(f"🎬 Director: Switching to backup key #{self.current_key_index + 1}")
            self._init_client()
            return True
        return False

    def _generate_with_google_ai(self, system_prompt: str, user_prompt: str, sections: list) -> dict:
        """Fallback to Google AI Studio."""
        if not self.google_model:
            return None
            
        logging.info("🌟 Director: Trying Google AI Studio fallback...")
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.google_model.generate_content(full_prompt)
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            result = json.loads(text.strip())
            logging.info("✅ Director: Google AI Studio succeeded!")
            return result
            
        except Exception as e:
            logging.error(f"❌ Director: Google AI Studio failed: {e}")
            # Return Japanese-themed fallback
            return {
                "mood": "zen",
                "scenes": {k: "Cherry blossoms floating softly zen garden peaceful" for k in sections}
            }

    def _get_best_free_models(self) -> list:
        """Discovers best free models on OpenRouter."""
        try:
            logging.info("🎬 Director: Discovering best free models...")
            response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
            if response.status_code != 200:
                return ["google/gemini-2.0-flash-exp:free"]
            
            all_models = response.json().get("data", [])
            free_models = []
            
            for m in all_models:
                pricing = m.get("pricing", {})
                if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                    free_models.append(m["id"])
            
            scored = []
            for mid in free_models:
                score = 0
                ml = mid.lower()
                if "gemini" in ml: score += 10
                if "llama-3" in ml: score += 8
                if "flash" in ml: score += 3
                if "nano" in ml or "1b" in ml: score -= 20
                scored.append((score, mid))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            best = [m[1] for m in scored[:3]]
            logging.info(f"🎬 Director: Using models: {best}")
            return best if best else ["google/gemini-2.0-flash-exp:free"]
            
        except Exception as e:
            logging.warning(f"Model discovery failed: {e}")
            return ["google/gemini-2.0-flash-exp:free"]

    def create_screenplay(self, script_data) -> dict:
        """
        Analyzes the fortune script and generates Japanese-themed visual keywords.
        """
        logging.info("🎬 Director: Creating Japanese visual screenplay...")
        
        sections = ["hook", "love", "career", "money", "health", "lucky_item"]
        
        if isinstance(script_data, dict):
            full_script_text = " ".join([str(script_data.get(k, "")) for k in sections if k in script_data])
        elif isinstance(script_data, list):
            full_script_text = " ".join([str(item) for item in script_data if item])
        else:
            full_script_text = str(script_data)
        
        system_prompt = """
You are a Japanese Visual Director specializing in 占い (fortune-telling) video aesthetics.
You transform fortune scripts into CINEMATIC JAPANESE VISUALS.

Your visual vocabulary includes:
- 桜 (Sakura): Cherry blossoms, petals floating, spring atmosphere
- 神社 (Jinja): Shinto shrines, torii gates, sacred spaces
- 禅 (Zen): Zen gardens, rock gardens, meditation spaces
- 月 (Tsuki): Moon, moonlight, nighttime mysticism  
- 富士山: Mount Fuji, majestic landscapes
- 温泉: Onsen steam, relaxation imagery
- 提灯: Japanese lanterns, festival warmth
- 招き猫: Maneki-neko fortune cats

Rules for Keywords:
1. Use English but evoke JAPANESE aesthetics
2. Cinematic, atmospheric, high quality
3. NO text descriptions, pure visual mood
4. Match the emotion but stay authentically Japanese
"""
        
        user_prompt = f"""
Analyze this Japanese Fortune Script and generate visual keywords.

Script Context: {full_script_text[:500]}

Return ONLY JSON:
{{
    "mood": "zen" | "sakura" | "mystical" | "energetic" | "serene",
    "music_style": "Koto ambient" | "Shamisen upbeat" | "Zen meditation" | "Taiko drums",
    "scenes": {{
        "hook": "Japanese cinematic keyword for opening",
        "love": "Japanese romantic visual keyword",
        "career": "Japanese success/ambition visual keyword",
        "money": "Japanese prosperity visual keyword (maneki-neko, coins)",
        "health": "Japanese wellness visual keyword (onsen, zen)",
        "lucky_item": "Japanese fortune item visual"
    }}
}}
"""

        # --- PRIORITY 1: GOOGLE AI (Unlimited/Free Tier) ---
        import time 
        if self.google_model:
            logging.info("✨ Director: Using Google AI (Primary)...")
            google_result = self._generate_with_google_ai(system_prompt, user_prompt, sections)
            if google_result:
                logging.info("✅ Director: Google AI Generation Successful! Sleeping 60s to prevent rate limits...")
                time.sleep(60)
                return google_result
            else:
                logging.warning("⚠️ Director: Google AI Primary failed. Falling back to OpenRouter...")

        tried_backup = False
        daily_limit_hit = False
        
        for _loop in range(2):  # Max 2 loops instead of infinite
            if daily_limit_hit:
                break
                
            for model in self.models:
                if daily_limit_hit:
                    break
                    
                try:
                    logging.info(f"🎬 Director: Trying model {model}...")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    time.sleep(2) # Small break
                    return json.loads(response.choices[0].message.content)
                    
                except Exception as e:
                    error_str = str(e)
                    logging.warning(f"⚠️ Director model {model} failed: {e}")
                    
                    # Detect daily free limit exhaustion
                    if "free-models-per-day" in error_str.lower() or "Remaining\': \'0\'" in error_str:
                        logging.warning("🚫 Director: Daily free limit hit. Skipping OpenRouter.")
                        daily_limit_hit = True
                        break
                    
                    if "429" in error_str or "rate limit" in error_str.lower():
                        if not tried_backup and self._switch_to_backup_key():
                            logging.info("🔄 Rate limit hit! Retrying with backup key...")
                            tried_backup = True
                            break
                        else:
                             logging.info("⏳ Director sleeping 30s for rate limit...")
                             time.sleep(30)
                    continue
            else:
                # This 'else' block belongs to the inner 'for model' loop.
                # If the inner loop completes without a 'break' (meaning all models failed without rate limit/daily limit),
                # we should break the outer loop as well, or let it continue to the next iteration if _loop < 1.
                # Given the `daily_limit_hit` and `tried_backup` logic, if we reach here, it means all models failed
                # and no rate limit/daily limit was hit that would cause a retry or skip.
                # The outer loop `for _loop in range(2)` will naturally exit after 2 iterations if no success.
                pass # No explicit break needed here, the outer loop will handle it.
        
        # Ultimate fallback - Japanese themed
        logging.error("❌ All Director models failed. Using Japanese fallback visuals.")
        return {
            "mood": "zen",
            "scenes": {
                "hook": "Mystical torii gate sunrise fog ethereal",
                "love": "Couple cherry blossoms sunset romantic temple",
                "career": "Tokyo skyline success confidence morning",
                "money": "Golden maneki-neko coins prosperity traditional",
                "health": "Zen garden meditation peaceful bamboo",
                "lucky_item": "Omamori charm shrine spiritual protection"
            }
        }
