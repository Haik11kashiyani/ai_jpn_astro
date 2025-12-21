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

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DirectorAgent:
    """
    The Director Agent converts a script into a Visual Screenplay.
    It decides the 'Mood' and selects specific, cinematic keywords for stock footage.
    Auto-discovers the best free model on OpenRouter.
    Supports multiple API keys with automatic failover on rate limits.
    Falls back to Google AI Studio when OpenRouter is exhausted.
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
        """Fallback to Google AI Studio (Gemini) when OpenRouter fails."""
        if not self.google_model:
            return None
            
        logging.info("🌟 Director: Trying Google AI Studio (Gemini) as fallback...")
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
            return {"mood": "Peaceful", "scenes": {k: "Abstract golden particles slow motion" for k in sections}}

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
            
            # Score and rank
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
        Analyzes the horoscope script and generates a shot list.
        Handles both dict and list script formats.
        """
        logging.info("🎬 Director: visualizing the script...")
        
        sections = ["intro", "love", "career", "money", "health", "remedy"]
        
        # Handle different input types
        if isinstance(script_data, dict):
            full_script_text = " ".join([str(script_data.get(k, "")) for k in sections])
        elif isinstance(script_data, list):
            full_script_text = " ".join([str(item) for item in script_data if item])
        else:
            full_script_text = str(script_data)
        
        system_prompt = """
        You are a Christopher Nolan-esque Film Director.
        You transform simple text into CINEMATIC VISUALS.
        
        Your Goal: Select STOCK FOOTAGE keywords that match the emotion but are NOT cheesy.
        
        Rules for Keywords:
        1. Always English.
        2. Visual, Atmospheric, High Quality.
        3. NO text on screen descriptions.
        4. Examples:
           - Bad: "Sad man" -> Good: "Silhouette in rain window reflection dark, moody"
           - Bad: "Money" -> Good: "Golden coins falling slow motion cinematic lighting"
           - Bad: "Love" -> Good: "Couple holding hands sunset silhouette beach"
        """
        
        user_prompt = f"""
        Analyze this Hindi Horoscope Script and generate a JSON Screenplay.
        
        Script Context: {full_script_text}
        
        Return ONLY a JSON object with this structure:
        {{
            "mood": "Mysterious" | "Energetic" | "Peaceful" | "Dark",
            "music_style": "Ambient Drone" | "Upbeat classical" | "Deep meditation",
            "scenes": {{
                "intro": "cinematic keyword 1",
                "love": "cinematic keyword 2",
                "career": "cinematic keyword 3",
                "money": "cinematic keyword 4",
                "health": "cinematic keyword 5",
                "remedy": "cinematic keyword 6"
            }}
        }}
        """

        tried_backup = False
        
        while True:
            for model in self.models:
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
                    
                    return json.loads(response.choices[0].message.content)
                    
                except Exception as e:
                    error_str = str(e)
                    logging.warning(f"⚠️ Director model {model} failed: {e}")
                    
                    # Check if it's a rate limit error (429)
                    if "429" in error_str or "rate limit" in error_str.lower():
                        if not tried_backup and self._switch_to_backup_key():
                            logging.info("🔄 Rate limit hit! Retrying with backup key...")
                            tried_backup = True
                            break  # Restart model loop with new key
                    continue
            else:
                # All models exhausted
                break
        
        # FINAL FALLBACK: Try Google AI Studio
        logging.warning("⚠️ Director: All OpenRouter models/keys exhausted. Trying Google AI...")
        google_result = self._generate_with_google_ai(system_prompt, user_prompt, sections)
        if google_result:
            return google_result
        
        # Ultimate fallback visuals
        logging.error("❌ All Director models/keys/fallbacks failed. Using hardcoded visuals.")
        return {
            "mood": "Peaceful",
            "scenes": {k: "Abstract golden particles slow motion" for k in sections}
        }
