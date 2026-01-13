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
# Updated to match actual PNG filenames in assets folder
RASHI_IMAGE_MAP = {
    "mesh": "mesh", "aries": "mesh",
    "vrushabh": "vrishabh", "vrishabh": "vrishabh", "taurus": "vrishabh",
    "mithun": "mithun", "gemini": "mithun",
    "kark": "kark", "cancer": "kark",
    "singh": "singh", "leo": "singh",
    "kanya": "kanya", "virgo": "kanya",
    "tula": "tula", "libra": "tula",
    "vrushchik": "vrishchik", "vrishchik": "vrishchik", "scorpio": "vrishchik",
    "dhanu": "dhanu", "sagittarius": "dhanu",
    "makar": "makar", "capricorn": "makar",
    "kumbh": "kumbh", "aquarius": "kumbh",
    "meen": "meen", "pisces": "meen",
}

# Rashi-themed Deep Gradients (Top, Middle, Bottom)
RASHI_STYLES = {
    # Fire Signs (Dynamic Red/Orange/Gold)
    "mesh":      {"grad": ("#4a0e0e", "#801515", "#fbb03b"), "glow": "#ff4500", "element": "fire"},
    "aries":     {"grad": ("#4a0e0e", "#801515", "#fbb03b"), "glow": "#ff4500", "element": "fire"},
    "singh":     {"grad": ("#3e1e07", "#8e4010", "#f5d300"), "glow": "#ffd700", "element": "fire"},
    "leo":       {"grad": ("#3e1e07", "#8e4010", "#f5d300"), "glow": "#ffd700", "element": "fire"},
    "dhanu":     {"grad": ("#2b1338", "#6a1b9a", "#ff8f00"), "grad_note": "Purple to Orange", "glow": "#ffa500", "element": "fire"},
    "sagittarius":{"grad": ("#2b1338", "#6a1b9a", "#ff8f00"), "glow": "#ffa500", "element": "fire"},
    
    # Earth Signs (Rich Green/Brown/Emerald)
    "vrushabh":  {"grad": ("#0f2214", "#2e7d32", "#a5d6a7"), "glow": "#4caf50", "element": "earth"},
    "taurus":    {"grad": ("#0f2214", "#2e7d32", "#a5d6a7"), "glow": "#4caf50", "element": "earth"},
    "kanya":     {"grad": ("#1b2e1b", "#558b2f", "#cddc39"), "glow": "#8bc34a", "element": "earth"},
    "virgo":     {"grad": ("#1b2e1b", "#558b2f", "#cddc39"), "glow": "#8bc34a", "element": "earth"},
    "makar":     {"grad": ("#101010", "#424242", "#90a4ae"), "glow": "#b0bec5", "element": "earth"},
    "capricorn": {"grad": ("#101010", "#424242", "#90a4ae"), "glow": "#b0bec5", "element": "earth"},

    # Air Signs (Sky Blue/Lavender/Silver)
    "mithun":    {"grad": ("#1a237e", "#3949ab", "#ffeb3b"), "glow": "#ffff00", "element": "air"},
    "gemini":    {"grad": ("#1a237e", "#3949ab", "#ffeb3b"), "glow": "#ffff00", "element": "air"},
    "tula":      {"grad": ("#251034", "#6a1b9a", "#f8bbd0"), "glow": "#ff80ab", "element": "air"},
    "libra":     {"grad": ("#251034", "#6a1b9a", "#f8bbd0"), "glow": "#ff80ab", "element": "air"},
    "kumbh":     {"grad": ("#001030", "#0277bd", "#4fc3f7"), "glow": "#29b6f6", "element": "air"},
    "aquarius":  {"grad": ("#001030", "#0277bd", "#4fc3f7"), "glow": "#29b6f6", "element": "air"},

    # Water Signs (Deep Blue/Teal/Mystic)
    "kark":      {"grad": ("#0d1526", "#1565c0", "#90caf9"), "glow": "#e3f2fd", "element": "water"},
    "cancer":    {"grad": ("#0d1526", "#1565c0", "#90caf9"), "glow": "#e3f2fd", "element": "water"},
    "vrushchik": {"grad": ("#200508", "#880e4f", "#ff1744"), "glow": "#ff5252", "element": "water"},
    "scorpio":   {"grad": ("#200508", "#880e4f", "#ff1744"), "glow": "#ff5252", "element": "water"},
    "meen":      {"grad": ("#002025", "#006064", "#1de9b6"), "glow": "#64ffda", "element": "water"},
    "pisces":    {"grad": ("#002025", "#006064", "#1de9b6"), "glow": "#64ffda", "element": "water"},
}

# Dynamic Lucky Color Themes (Overrides Rashi defaults)
COLOR_STYLES = {
    "red":    {"grad": ("#2b0505", "#8a0a0a", "#ff5252"), "glow": "#ff0000", "element": "fire"},
    "blue":   {"grad": ("#050a2b", "#0a2a8a", "#52b6ff"), "glow": "#00bfff", "element": "water"},
    "green":  {"grad": ("#052b0a", "#0a8a1a", "#52ff70"), "glow": "#00ff00", "element": "earth"},
    "yellow": {"grad": ("#2b2005", "#8a6a0a", "#ffeb3b"), "glow": "#ffd700", "element": "air"},
    "white":  {"grad": ("#202020", "#808080", "#ffffff"), "glow": "#ffffff", "element": "air"},
    "black":  {"grad": ("#000000", "#202020", "#404040"), "glow": "#808080", "element": "earth"},
    "pink":   {"grad": ("#2b0515", "#8a0a4a", "#ff52a2"), "glow": "#ff69b4", "element": "fire"},
    "orange": {"grad": ("#2b1505", "#8a450a", "#ff9552"), "glow": "#ffa500", "element": "fire"},
    "purple": {"grad": ("#15052b", "#4a0a8a", "#a252ff"), "glow": "#800080", "element": "air"},
    "brown":  {"grad": ("#1a1005", "#4e342e", "#8d6e63"), "glow": "#a1887f", "element": "earth"},
    "gold":   {"grad": ("#2b2005", "#8a6a0a", "#ffd700"), "glow": "#ffd700", "element": "fire"},
    "silver": {"grad": ("#101520", "#546e7a", "#cfd8dc"), "glow": "#b0bec5", "element": "water"},
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

    def get_rashi_image_path(self, rashi_name: str, period_type: str = "Daily") -> str:
        """
        Finds the appropriate rashi image using fuzzy matching.
        """
        rashi_key = self._get_rashi_key(rashi_name)
        alt_key = ""
        if "(" in rashi_name:
            alt_key = rashi_name.split("(")[1].replace(")", "").strip().lower()

        # Folders to search in order
        folders = ["12_photos"]
        if period_type == "Monthly": folders.insert(0, "monthly_12_photos")
        elif period_type == "Yearly": folders.insert(0, "yearly_12_photos")
        
        search_keys = [rashi_key, alt_key] if alt_key else [rashi_key]
        
        for folder in folders:
            folder_path = os.path.join("assets", folder)
            if not os.path.exists(folder_path): continue
            
            # List all files for case-insensitive matching
            try:
                files = os.listdir(folder_path)
                for f in files:
                    fname_lower = f.lower()
                    for key in search_keys:
                        if key and key in fname_lower: # Looser match: "mesh" in "mesh_daily.jpg"
                             return os.path.abspath(os.path.join(folder_path, f))
            except Exception as e:
                logging.warning(f"Error scanning folder {folder}: {e}")
                
        # Final fallback: Look for ANY image with the key in 'assets' root if needed (optional)
        return None

    async def _render_html_scene(self, rashi_name, text, duration, subtitle_data, theme_override=None, header_text="", period_type="Daily", anim_style="premium"):
        """
        Renders the scene using Playwright.
        Captures screenshots at 30 FPS.
        """
        frames_dir = f"assets/temp/frames_{hash(text)}"
        os.makedirs(frames_dir, exist_ok=True)
        
        # Prepare params
        # rashi_name comes in as "Mesh" (cleaned) or "Mesh (Aries)"
        rashi_img = self.get_rashi_image_path(rashi_name, period_type) or ""
        rashi_key = self._get_rashi_key(rashi_name)
        
        # Get style: COLOR_THEME > RASHI_STYLES > Fallback
        style = None
        if theme_override and theme_override in COLOR_STYLES:
            style = COLOR_STYLES[theme_override]
        
        if not style:
             style = RASHI_STYLES.get(rashi_key)
             
        if not style:
             # Fallback
             style = {"grad": ("#303060", "#202040", "#101020"), "glow": "#ffffff", "element": "neutral"}
        
        grad = style["grad"] # (c1, c2, c3)
        glow = style["glow"]
        element = style["element"]
        
        # Convert local path to file URL for browser
        if rashi_img:
            rashi_img_url = f"file:///{rashi_img.replace(os.sep, '/')}"
        else:
            rashi_img_url = ""
            
        # Construct URL with new params
        # Ensure text is properly encoded
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        encoded_header = urllib.parse.quote(header_text)
        
        # Add animation style to URL
        url = (f"file:///{self.template_path.replace(os.sep, '/')}?text={encoded_text}&header={encoded_header}&img={rashi_img_url}"
               f"&c1={grad[0].replace('#', '%23')}&c2={grad[1].replace('#', '%23')}&c3={grad[2].replace('#', '%23')}"
               f"&glow={glow.replace('#', '%23')}&elem={element}&anim={anim_style}")
        
        logging.info(f"   🌍 Launching Playwright ({anim_style.upper()}) for scene ({duration}s)...")
        
        frames = []
        fps = 30
        total_frames = int(duration * fps)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = await browser.new_page(viewport={"width": 1080, "height": 1920})
            
            
            await page.goto(url)
            # Wait for text to actually appear
            await page.wait_for_selector(f"#text-container") 
            
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

    def create_scene(self, rashi_name: str, text: str, duration: float, subtitle_data: list = None, theme_override: str = None, header_text: str = "", period_type: str = "Daily"):
        """Wrapper to run async render synchronously. Randomizes animation style."""
        import random
        # Randomize animation style per scene
        anim_styles = ['premium', 'cine', 'type', 'pop', 'slide']
        chosen_style = random.choice(anim_styles)
        
        try:
            frames = asyncio.run(self._render_html_scene(rashi_name, text, duration, subtitle_data, theme_override, header_text, period_type, chosen_style))
            
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
        
        # --- STRICT 59 SECOND LIMIT ---
        MAX_DURATION = 59.0
        if final_video.duration > MAX_DURATION:
            logging.warning(f"⚠️ Video duration {final_video.duration}s exceeds {MAX_DURATION}s. Trimming...")
            # Trim to absolute max
            final_video = final_video.subclip(0, MAX_DURATION)
            # Short fadeout only at the very end
            final_video = final_video.fadeout(0.2)
        else:
            # If within limits, minimal padding to ensure audio finish, just in case
            pass
        # ------------------------------ 
        
        # Add background music
        # USER REQUEST: Removed music ("very o full")
        # bg_music_path = self._select_music_by_mood(mood)
        # if bg_music_path and os.path.exists(bg_music_path):
        #     try:
        #         bg_music = AudioFileClip(bg_music_path)
        #         if bg_music.duration < final_video.duration:
        #             bg_music = vfx.loop(bg_music, duration=final_video.duration)
        #         else:
        #             bg_music = bg_music.subclip(0, final_video.duration)
        #         
        #         bg_music = bg_music.volumex(0.20)
        #         
        #         if final_video.audio:
        #             final_audio = CompositeAudioClip([final_video.audio, bg_music])
        #             final_video = final_video.set_audio(final_audio)
        #         else:
        #             final_video = final_video.set_audio(bg_music)
        #         logging.info(f"   🎵 Music added: {os.path.basename(bg_music_path)}")
        #     except Exception as e:
        #         logging.error(f"   ⚠️ Music error: {e}")
        
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

# Helper for concatenate to avoid circular dependencies if any
def run_concatenate(clips):
    from moviepy.editor import concatenate_videoclips
    return concatenate_videoclips(clips, method="compose")
