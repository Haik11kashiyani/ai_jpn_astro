import os
import logging
import json
import asyncio
import nest_asyncio
from playwright.async_api import async_playwright
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip, vfx, CompositeVideoClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Allow nested asyncio loops (required for Playwright in some envs)
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rashi name to filename mapping
RASHI_IMAGE_MAP = {
    "mesh": "mesh.jpg", "aries": "mesh.jpg",
    "vrushabh": "vrushabh.jpg", "taurus": "vrushabh.jpg",
    "mithun": "mithun.jpg", "gemini": "mithun.jpg",
    "kark": "kark.jpg", "cancer": "kark.jpg",
    "singh": "singh.jpg", "leo": "singh.jpg",
    "kanya": "kanya.jpg", "virgo": "kanya.jpg",
    "tula": "tula.jpg", "libra": "tula.jpg",
    "vrushchik": "vrushchik.jpg", "scorpio": "vrushchik.jpg",
    "dhanu": "dhanu.jpg", "sagittarius": "dhanu.jpg",
    "makar": "makar.jpg", "capricorn": "makar.jpg",
    "kumbh": "kumbh.jpg", "aquarius": "kumbh.jpg",
    "meen": "meen.jpg", "pisces": "meen.jpg",
}

# Rashi-themed gradient colors (top_color, bottom_color)
RASHI_GRADIENTS = {
    "mesh": ("#B42828", "#3C0A0A"),       # Red/maroon
    "aries": ("#B42828", "#3C0A0A"),
    "vrushabh": ("#28783C", "#0F3219"),   # Green
    "taurus": ("#28783C", "#0F3219"),
    "mithun": ("#C8B432", "#503C14"),    # Yellow
    "gemini": ("#C8B432", "#503C14"),
    "kark": ("#3C508C", "#141E3C"),       # Blue
    "cancer": ("#3C508C", "#141E3C"),
    "singh": ("#C8641E", "#50280A"),     # Orange
    "leo": ("#C8641E", "#50280A"),
    "kanya": ("#648C50", "#283C1E"),     # Olive
    "virgo": ("#648C50", "#283C1E"),
    "tula": ("#8C64A0", "#32233C"),     # Purple
    "libra": ("#8C64A0", "#32233C"),
    "vrushchik": ("#641E28", "#280A0F"),  # Dark red
    "scorpio": ("#641E28", "#280A0F"),
    "dhanu": ("#A05028", "#3C1E0F"),      # Brown
    "sagittarius": ("#A05028", "#3C1E0F"),
    "makar": ("#3C3C3C", "#191919"),       # Gray
    "capricorn": ("#3C3C3C", "#191919"),
    "kumbh": ("#2864A0", "#0F283C"),     # Blue
    "aquarius": ("#2864A0", "#0F283C"),
    "meen": ("#50788C", "#1E323C"),      # Teal
    "pisces": ("#50788C", "#1E323C"),
}

class EditorEngine:
    """
    Premium HYBRID Video Engine.
    Uses Playwright (Headless Chrome) to render HTML5 animations to valid video frames.
    Compiles with MoviePy.
    """
    
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.template_path = os.path.abspath("templates/scene.html")
        os.makedirs("assets/temp", exist_ok=True)

    def _get_rashi_key(self, rashi_name: str) -> str:
        """Extract rashi key from name like 'Mesh (Aries)'."""
        rashi_key = rashi_name.lower().split()[0].split("(")[0].strip()
        return rashi_key

    def get_rashi_image_path(self, rashi_name: str) -> str:
        """Finds the appropriate rashi image from the 12_photos folder."""
        rashi_key = self._get_rashi_key(rashi_name)
        if "(" in rashi_name:
            alt_key = rashi_name.split("(")[1].replace(")", "").strip().lower()
        else:
            alt_key = rashi_key
        filename = RASHI_IMAGE_MAP.get(rashi_key) or RASHI_IMAGE_MAP.get(alt_key)
        if filename:
            path = os.path.join("assets", "12_photos", filename)
            if os.path.exists(path):
                return os.path.abspath(path) # Must be absolute for HTML
        return None

    async def _render_html_scene(self, rashi_name, text, duration, subtitle_data):
        """
        Renders the scene using Playwright.
        Captures screenshots at 30 FPS.
        """
        frames_dir = f"assets/temp/frames_{hash(text)}"
        os.makedirs(frames_dir, exist_ok=True)
        
        # Prepare params
        rashi_img = self.get_rashi_image_path(rashi_name) or ""
        rashi_key = self._get_rashi_key(rashi_name)
        colors = RASHI_GRADIENTS.get(rashi_key, ("#303060", "#101020"))
        
        # Convert local path to file URL for browser
        if rashi_img:
            rashi_img_url = f"file:///{rashi_img.replace(os.sep, '/')}"
        else:
            rashi_img_url = ""
            
        url = f"file:///{self.template_path.replace(os.sep, '/')}?text={text}&img={rashi_img_url}&c1={colors[0].replace('#', '%23')}&c2={colors[1].replace('#', '%23')}"
        
        logging.info(f"   🌍 Launching Playwright for scene ({duration}s)...")
        
        frames = []
        fps = 30
        total_frames = int(duration * fps)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1080, "height": 1920})
            
            await page.goto(url)
            await page.wait_for_selector("#text-container") # Wait for load
            
            logging.info(f"   📸 Capturing {total_frames} frames...")
            
            for i in range(total_frames):
                current_time = i / fps
                
                # 1. Update Karaoke Highlight
                if subtitle_data:
                    # Find which word should be active
                    active_idx = -1
                    for idx, sub in enumerate(subtitle_data):
                        if sub['start'] <= current_time < (sub['start'] + sub['duration']):
                            active_idx = idx
                            break
                    
                    if active_idx != -1:
                         await page.evaluate(f"window.setWordActive({active_idx})")
                
                # 2. Update Animations (GSAP seek)
                await page.evaluate(f"window.seek({current_time})")
                
                # 3. Capture Frame
                frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
                await page.screenshot(path=frame_path, type='png')
                frames.append(frame_path)
            
            await browser.close()
            
        return frames

    def create_scene(self, rashi_name: str, text: str, duration: float, subtitle_data: list = None):
        """Wrapper to run async render synchronously."""
        try:
            frames = asyncio.run(self._render_html_scene(rashi_name, text, duration, subtitle_data))
            
            if not frames:
                raise Exception("No frames captured")
                
            # Create video clip from frames
            clip = ImageSequenceClip(frames, fps=30)
            return clip
            
        except Exception as e:
            logging.error(f"❌ Playwright Render Error: {e}")
            # Fallback to simple image if playwright fails
            return None # Main loop will handle or crash

    def assemble_final(self, scenes: list, output_path: str, mood: str = "peaceful"):
        """Assembles all scenes and adds background music."""
        if not scenes:
            logging.error("No scenes to assemble!")
            return
            
        # Filter None scenes
        scenes = [s for s in scenes if s is not None]
        if not scenes:
            logging.error("All scenes failed to render.")
            return

        logging.info(f"🎬 Assembling {len(scenes)} scenes...")
        # Use simple concatenate for performance
        final_video = run_concatenate(scenes) 
        
        # Add background music
        bg_music_path = self._select_music_by_mood(mood)
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                if bg_music.duration < final_video.duration:
                    bg_music = vfx.loop(bg_music, duration=final_video.duration)
                else:
                    bg_music = bg_music.subclip(0, final_video.duration)
                
                bg_music = bg_music.volumex(0.20)
                
                if final_video.audio:
                    final_audio = CompositeAudioClip([final_video.audio, bg_music])
                    final_video = final_video.set_audio(final_audio)
                else:
                    final_video = final_video.set_audio(bg_music)
                logging.info(f"   🎵 Music added: {os.path.basename(bg_music_path)}")
            except Exception as e:
                logging.error(f"   ⚠️ Music error: {e}")
        
        # Write final video
        logging.info(f"   📹 Rendering to {output_path}...")
        final_video.write_videofile(
            output_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            preset="medium"
        )
        logging.info(f"   ✅ Video saved: {output_path}")

    def _select_music_by_mood(self, mood: str) -> str:
        """Selects background music based on mood."""
        import random
        music_folder = os.path.join("assets", "music")
        if not os.path.exists(music_folder):
            os.makedirs(music_folder, exist_ok=True)
            self._ensure_music_assets(music_folder)
        
        all_music = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav', '.m4a'))]
        if not all_music:
            self._ensure_music_assets(music_folder)
            all_music = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav', '.m4a'))]
        
        if not all_music: return None

        mood_lower = mood.lower()
        matching_music = [f for f in all_music if mood_lower in f.lower()]
        
        if not matching_music:
            if "energetic" in mood_lower: matching_music = [f for f in all_music if "upbeat" in f.lower()]
            elif "peaceful" in mood_lower: matching_music = [f for f in all_music if "ambient" in f.lower()]
             
        target_list = matching_music if matching_music else all_music
        return os.path.join(music_folder, random.choice(target_list))

    def _ensure_music_assets(self, music_folder):
        """Downloads default royalty-free music."""
        tracks = {
            "peaceful_ambient.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Clean%20Soul.mp3",
            "energetic_upbeat.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Life%20of%20Riley.mp3",
            "mysterious_deep.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Private%20Reflection.mp3"
        }
        try:
            import requests
            for f, u in tracks.items():
                p = os.path.join(music_folder, f)
                if not os.path.exists(p):
                    logging.info(f"   ⬇️ Fetching {f}...")
                    r = requests.get(u, verify=False, timeout=30)
                    with open(p, 'wb') as file: file.write(r.content)
        except Exception as e:
            logging.warning(f"   ⚠️ Could not download music: {e}")
        if not matching_music:
            if "energetic" in mood_lower or "happy" in mood_lower:
                matching_music = [f for f in all_music if "upbeat" in f.lower() or "fast" in f.lower()]
            elif "peaceful" in mood_lower or "calm" in mood_lower:
                matching_music = [f for f in all_music if "ambient" in f.lower() or "soft" in f.lower()]
            elif "mysterious" in mood_lower:
                matching_music = [f for f in all_music if "dark" in f.lower() or "slow" in f.lower()]
        
        # If still no match, pick random but prefer not 'intro' or 'outro' specific tracks if possible
        if not matching_music:
            logging.warning(f"   ⚠️ No specific music found for mood '{mood}', picking random.")
            target_list = all_music
        else:
            target_list = matching_music
            
        selected = random.choice(target_list)
        return os.path.join(music_folder, selected)
