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
        self.rate = "+0%"  # Reset to default for better emotion
        self.pitch = "+0Hz"

    async def generate_audio(self, text: str, output_path: str):
        """
        Generates MP3 audio and saves word-level subtitles to a JSON file.
        """
        # Clean text: Remove brackets and their content (e.g. "(Hook)")
        import re
        clean_text = re.sub(r'\s*\(.*?\)\s*', ' ', text).strip()
        if not clean_text: return False
        
        logging.info(f"🎙️ Narrator: Speaking {len(clean_text)} chars...")
        subtitle_path = output_path.replace(".mp3", ".json")
        
        # Retry logic for EdgeTTS
        for attempt in range(3):
            try:
                # Use default rate/pitch to minimize errors
                communicate = edge_tts.Communicate(clean_text, self.voice, rate=self.rate, pitch=self.pitch)
                subtitles = []
                
                with open(output_path, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            subtitles.append({
                                "text": chunk["text"],
                                "start": chunk["offset"] / 10000000, 
                                "duration": chunk["duration"] / 10000000
                            })
                
                # Check file integrity
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    # Save subtitles
                    if subtitles:
                        with open(subtitle_path, "w", encoding="utf-8") as f:
                            json.dump(subtitles, f, ensure_ascii=False, indent=2)
                    logging.info(f"   ✅ EdgeTTS Audio saved: {output_path}")
                    return True
                
            except Exception as e:
                logging.warning(f"⚠️ EdgeTTS Attempt {attempt+1} Failed: {e}")
                await asyncio.sleep(2) # Wait before retry

        logging.warning("⚠️ All EdgeTTS attempts failed. Switching to Fallback (gTTS)...")
        # Cleanup broken file if any
        if os.path.exists(output_path): os.remove(output_path)
            
        return self._fallback_gtts(clean_text, output_path, subtitle_path)

    def _fallback_gtts(self, text: str, output_path: str, subtitle_path: str) -> bool:
        """Fallback using Google Text-to-Speech (gTTS) with pseudo-subtitles."""
        try:
            from gtts import gTTS
            from mutagen.mp3 import MP3
            
            tts = gTTS(text=text, lang='hi', slow=False)
            tts.save(output_path)
            
            if os.path.exists(output_path):
                # Generate Pseudo-Subtitles for highlighting
                try:
                    audio = MP3(output_path)
                    duration = audio.info.length
                    words = text.split()
                    word_duration = duration / max(len(words), 1)
                    
                    subtitles = []
                    current_time = 0.0
                    for word in words:
                        subtitles.append({
                            "text": word,
                            "start": current_time,
                            "duration": word_duration
                        })
                        current_time += word_duration
                        
                    with open(subtitle_path, "w", encoding="utf-8") as f:
                        json.dump(subtitles, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    logging.warning(f"⚠️ Could not generate pseudo-subtitles: {e}")

                logging.info(f"   ✅ gTTS Fallback Audio saved: {output_path}")
                return True
            return False
        except Exception as e:
            logging.error(f"❌ gTTS Fallback Failed: {e}")
            return False

    def speak(self, text: str, output_path: str):
        """Synchronous wrapper for async speak."""
        asyncio.run(self.generate_audio(text, output_path))
