import os
import json
import asyncio
import edge_tts
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NarratorAgent:
    """
    The Narrator Agent uses Edge-TTS (Neural) to generate human-like Hindi voiceovers.
    """
    
    def __init__(self):
        # Neural Voices: hi-IN-SwaraNeural (Female) or hi-IN-MadhurNeural (Male)
        self.voice = "hi-IN-SwaraNeural"
        self.rate = "+25%"  # Faster delivery for Shorts style
        self.pitch = "+0Hz"

    async def generate_audio(self, text: str, output_path: str):
        """
        Generates MP3 audio and saves word-level subtitles to a JSON file.
        """
        logging.info(f"🎙️ Narrator: Speaking {len(text)} chars...")
        subtitle_path = output_path.replace(".mp3", ".json")
        
        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            subtitles = []
            
            with open(output_path, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        subtitles.append({
                            "text": chunk["text"],
                            "start": chunk["offset"] / 10000000, # 100ns units to seconds
                            "duration": chunk["duration"] / 10000000
                        })
            
            # Save subtitles
            if subtitles:
                with open(subtitle_path, "w", encoding="utf-8") as f:
                    json.dump(subtitles, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(output_path):
                logging.info(f"   ✅ Audio saved: {output_path}")
                logging.info(f"   ✅ Subtitles saved: {subtitle_path}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"❌ Narrator Failed: {e}")
            return False

    def speak(self, text: str, output_path: str):
        """Synchronous wrapper for async speak."""
        asyncio.run(self.generate_audio(text, output_path))
