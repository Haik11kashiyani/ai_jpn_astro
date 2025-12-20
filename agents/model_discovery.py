"""
Model Discovery Agent - Automatically finds the best free model on OpenRouter.
"""
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cache the model to avoid repeated API calls
_cached_model = None

def get_best_free_model(api_key: str = None) -> str:
    """
    Fetches the list of models from OpenRouter and returns the best free model.
    Prioritizes: capability, context length, and being free.
    """
    global _cached_model
    
    if _cached_model:
        return _cached_model
    
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        logging.warning("No API key, using default model.")
        return "google/gemini-2.0-flash-thinking-exp:free"
    
    try:
        logging.info("🔍 Discovering best free model on OpenRouter...")
        
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        
        if response.status_code != 200:
            logging.warning(f"Failed to fetch models: {response.status_code}")
            return "google/gemini-2.0-flash-thinking-exp:free"
        
        models = response.json().get("data", [])
        
        # Filter for free models (pricing.prompt == "0" or very low)
        free_models = []
        for model in models:
            pricing = model.get("pricing", {})
            prompt_cost = float(pricing.get("prompt", "1") or "1")
            completion_cost = float(pricing.get("completion", "1") or "1")
            
            # Consider "free" if both costs are 0 or negligible
            if prompt_cost == 0 and completion_cost == 0:
                free_models.append(model)
        
        if not free_models:
            logging.warning("No free models found, using default.")
            return "google/gemini-2.0-flash-thinking-exp:free"
        
        # Sort by context length (higher is better for long content)
        free_models.sort(key=lambda m: m.get("context_length", 0), reverse=True)
        
        # Prefer models with good names (gemini, claude, gpt, llama, etc.)
        preferred_keywords = ["gemini", "claude", "gpt", "llama", "mixtral", "qwen"]
        
        best_model = None
        for model in free_models:
            model_id = model.get("id", "").lower()
            for keyword in preferred_keywords:
                if keyword in model_id:
                    best_model = model
                    break
            if best_model:
                break
        
        # Fallback to first free model if no preferred found
        if not best_model:
            best_model = free_models[0]
        
        model_id = best_model.get("id")
        context_len = best_model.get("context_length", "?")
        
        logging.info(f"✅ Best Free Model: {model_id} (Context: {context_len})")
        
        _cached_model = model_id
        return model_id
        
    except Exception as e:
        logging.error(f"Model discovery failed: {e}")
        return "google/gemini-2.0-flash-thinking-exp:free"


def clear_cache():
    """Clears the cached model (useful for testing)."""
    global _cached_model
    _cached_model = None
