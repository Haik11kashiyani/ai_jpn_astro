import os
import json
import asyncio
import edge_tts
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NarratorAgent:
    """
    The Narrator Agent uses Edge-TTS (Neural) to generate human-like Japanese voiceovers.
    Uses ja-JP-NanamiNeural for natural, warm female Japanese voice.
    """
    
    def __init__(self):
        # Japanese Neural Voices:
        # ja-JP-NanamiNeural (Female) - Most natural, warm tone
        # ja-JP-KeitaNeural (Male) - Professional male voice
        self.voice = "ja-JP-NanamiNeural"
        self.rate = "-5%"   # Slightly slower for mystical feel
        self.pitch = "+0Hz"

    async def generate_audio(self, text: str, output_path: str):
        """
        Generates MP3 audio and saves word-level subtitles to a JSON file.
        """
        # Clean text: Remove brackets and their content
        import re
        clean_text = re.sub(r'\s*\(.*?\)\s*', ' ', text).strip()
        if not clean_text: return False
        
        logging.info(f"🎙️ Narrator: Speaking {len(clean_text)} Japanese chars...")
        subtitle_path = output_path.replace(".mp3", ".json")
        
        # Retry logic for EdgeTTS
        for attempt in range(3):
            try:
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
                    if subtitles:
                        with open(subtitle_path, "w", encoding="utf-8") as f:
                            json.dump(subtitles, f, ensure_ascii=False, indent=2)
                    logging.info(f"   ✅ Japanese Audio saved: {output_path}")
                    return True
                
            except Exception as e:
                logging.warning(f"⚠️ EdgeTTS Attempt {attempt+1} Failed: {e}")
                await asyncio.sleep(2)

        logging.warning("⚠️ All EdgeTTS attempts failed. Switching to Fallback (gTTS)...")
        if os.path.exists(output_path): os.remove(output_path)
            
        return self._fallback_gtts(clean_text, output_path, subtitle_path)

    def _fallback_gtts(self, text: str, output_path: str, subtitle_path: str) -> bool:
        """Fallback using Google Text-to-Speech (gTTS) with pseudo-subtitles."""
        try:
            from gtts import gTTS
            from mutagen.mp3 import MP3
            
            # Use Japanese language
            tts = gTTS(text=text, lang='ja', slow=False)
            tts.save(output_path)
            
            if os.path.exists(output_path):
                try:
                    audio = MP3(output_path)
                    duration = audio.info.length
                    
                    # For Japanese, split by common particles and spaces
                    # Japanese doesn't have spaces, so we'll split by characters for pseudo-subtitles
                    # This is less accurate but works as fallback
                    import re
                    # Split by Japanese punctuation marks
                    words = re.split(r'([。、！？\s]+)', text)
                    words = [w for w in words if w.strip()]
                    
                    if not words:
                        words = list(text)  # Fallback to character-by-character
                    
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
