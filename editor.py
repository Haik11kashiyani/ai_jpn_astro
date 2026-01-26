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

# Eto (干支) Romaji to filename mapping
ETO_IMAGE_MAP = {
    "ne": "ne", "rat": "ne",
    "ushi": "ushi", "ox": "ushi",
    "tora": "tora", "tiger": "tora",
    "u": "u", "rabbit": "u",
    "tatsu": "tatsu", "dragon": "tatsu",
    "mi": "mi", "snake": "mi",
    "uma": "uma", "horse": "uma",
    "hitsuji": "hitsuji", "sheep": "hitsuji",
    "saru": "saru", "monkey": "saru",
    "tori": "tori", "rooster": "tori",
    "inu": "inu", "dog": "inu",
    "i": "i", "boar": "i",
}

# Japanese Traditional Colors (和色 Wairo) Themed Styles
ETO_STYLES = {
    # Water Element (水) - Deep ocean blues, teal
    "ne": {"grad": ("#0a1628", "#1e4066", "#5c9dc9"), "glow": "#4fb3d9", "element": "water"},
    "rat": {"grad": ("#0a1628", "#1e4066", "#5c9dc9"), "glow": "#4fb3d9", "element": "water"},
    "i": {"grad": ("#0a1628", "#1e4066", "#5c9dc9"), "glow": "#4fb3d9", "element": "water"},
    "boar": {"grad": ("#0a1628", "#1e4066", "#5c9dc9"), "glow": "#4fb3d9", "element": "water"},
    
    # Wood Element (木) - Forest greens, bamboo
    "tora": {"grad": ("#0f1f0a", "#2d5a1e", "#7cb342"), "glow": "#8bc34a", "element": "wood"},
    "tiger": {"grad": ("#0f1f0a", "#2d5a1e", "#7cb342"), "glow": "#8bc34a", "element": "wood"},
    "u": {"grad": ("#0f1f0a", "#2d5a1e", "#7cb342"), "glow": "#8bc34a", "element": "wood"},
    "rabbit": {"grad": ("#0f1f0a", "#2d5a1e", "#7cb342"), "glow": "#8bc34a", "element": "wood"},
    
    # Fire Element (火) - Sakura reds, passionate pinks
    "mi": {"grad": ("#2b0a14", "#8a1e3d", "#ff6b8a"), "glow": "#ff4081", "element": "fire"},
    "snake": {"grad": ("#2b0a14", "#8a1e3d", "#ff6b8a"), "glow": "#ff4081", "element": "fire"},
    "uma": {"grad": ("#2b0a14", "#8a1e3d", "#ff6b8a"), "glow": "#ff4081", "element": "fire"},
    "horse": {"grad": ("#2b0a14", "#8a1e3d", "#ff6b8a"), "glow": "#ff4081", "element": "fire"},
    
    # Earth Element (土) - Temple gold, warm browns  
    "ushi": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "ox": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "tatsu": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "dragon": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "hitsuji": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "sheep": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "inu": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    "dog": {"grad": ("#1a1409", "#4a3728", "#c9a66b"), "glow": "#d4a574", "element": "earth"},
    
    # Metal Element (金) - Silver, platinum, moonlight
    "saru": {"grad": ("#1a1a2e", "#3d3d5c", "#b0b0c9"), "glow": "#c9c9e0", "element": "metal"},
    "monkey": {"grad": ("#1a1a2e", "#3d3d5c", "#b0b0c9"), "glow": "#c9c9e0", "element": "metal"},
    "tori": {"grad": ("#1a1a2e", "#3d3d5c", "#b0b0c9"), "glow": "#c9c9e0", "element": "metal"},
    "rooster": {"grad": ("#1a1a2e", "#3d3d5c", "#b0b0c9"), "glow": "#c9c9e0", "element": "metal"},
}

# Dynamic Lucky Color Themes (Overrides Eto defaults when specified)
COLOR_STYLES = {
    "赤": {"grad": ("#2b0505", "#8a0a0a", "#ff5252"), "glow": "#ff0000", "element": "fire"},
    "red": {"grad": ("#2b0505", "#8a0a0a", "#ff5252"), "glow": "#ff0000", "element": "fire"},
    "青": {"grad": ("#050a2b", "#0a2a8a", "#52b6ff"), "glow": "#00bfff", "element": "water"},
    "blue": {"grad": ("#050a2b", "#0a2a8a", "#52b6ff"), "glow": "#00bfff", "element": "water"},
    "緑": {"grad": ("#052b0a", "#0a8a1a", "#52ff70"), "glow": "#00ff00", "element": "wood"},
    "green": {"grad": ("#052b0a", "#0a8a1a", "#52ff70"), "glow": "#00ff00", "element": "wood"},
    "黄": {"grad": ("#2b2005", "#8a6a0a", "#ffeb3b"), "glow": "#ffd700", "element": "earth"},
    "yellow": {"grad": ("#2b2005", "#8a6a0a", "#ffeb3b"), "glow": "#ffd700", "element": "earth"},
    "白": {"grad": ("#202020", "#606060", "#ffffff"), "glow": "#ffffff", "element": "metal"},
    "white": {"grad": ("#202020", "#606060", "#ffffff"), "glow": "#ffffff", "element": "metal"},
    "黒": {"grad": ("#000000", "#151515", "#303030"), "glow": "#606060", "element": "water"},
    "black": {"grad": ("#000000", "#151515", "#303030"), "glow": "#606060", "element": "water"},
    "ピンク": {"grad": ("#2b0515", "#8a0a4a", "#ff52a2"), "glow": "#ff69b4", "element": "fire"},
    "pink": {"grad": ("#2b0515", "#8a0a4a", "#ff52a2"), "glow": "#ff69b4", "element": "fire"},
    "オレンジ": {"grad": ("#2b1505", "#8a450a", "#ff9552"), "glow": "#ffa500", "element": "fire"},
    "orange": {"grad": ("#2b1505", "#8a450a", "#ff9552"), "glow": "#ffa500", "element": "fire"},
    "紫": {"grad": ("#15052b", "#4a0a8a", "#a252ff"), "glow": "#800080", "element": "metal"},
    "purple": {"grad": ("#15052b", "#4a0a8a", "#a252ff"), "glow": "#800080", "element": "metal"},
    "金": {"grad": ("#2b2005", "#8a6a0a", "#ffd700"), "glow": "#ffd700", "element": "metal"},
    "gold": {"grad": ("#2b2005", "#8a6a0a", "#ffd700"), "glow": "#ffd700", "element": "metal"},
    "銀": {"grad": ("#101520", "#546e7a", "#cfd8dc"), "glow": "#b0bec5", "element": "metal"},
    "silver": {"grad": ("#101520", "#546e7a", "#cfd8dc"), "glow": "#b0bec5", "element": "metal"},
}

class EditorEngine:
    """
    Premium Japanese-Themed Video Engine.
    Uses Playwright (Headless Chrome) to render HTML5 animations.
    Features: Cherry blossoms, wave patterns, washi paper textures.
    """
    
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.template_path = os.path.abspath("templates/scene.html")
        os.makedirs("assets/temp", exist_ok=True)

    def _get_eto_key(self, eto_name: str) -> str:
        """Extract eto key from name like 'Ne (Rat/子)'."""
        eto_key = eto_name.lower().split()[0].split("(")[0].strip()
        return eto_key

    def get_eto_image_path(self, eto_name: str, period_type: str = "Daily") -> str:
        """
        Finds the appropriate Eto animal image.
        Searches in: eto_daily, eto_monthly, eto_yearly folders
        """
        eto_key = self._get_eto_key(eto_name)
        
        # Folders to search in order based on period type
        folders = ["eto_daily"]
        if period_type == "Monthly": 
            folders.insert(0, "eto_monthly")
        elif period_type == "Yearly": 
            folders.insert(0, "eto_yearly")
        
        # Get mapped filename
        mapped_key = ETO_IMAGE_MAP.get(eto_key, eto_key)
        
        # Search keys order
        search_keys = [mapped_key, eto_key]
        search_keys = list(dict.fromkeys(filter(None, search_keys)))
        
        for folder in folders:
            folder_path = os.path.join("assets", folder)
            if not os.path.exists(folder_path): 
                continue
            
            try:
                files = os.listdir(folder_path)
                for f in files:
                    fname_lower = f.lower()
                    # Check base name without extension
                    base_name = os.path.splitext(fname_lower)[0]
                    
                    for key in search_keys:
                        if key and key == base_name: # Exact match on name
                            return os.path.abspath(os.path.join(folder_path, f))
            except Exception as e:
                logging.warning(f"Error scanning folder {folder}: {e}")
        
        # Fallback: check 12_photos folder (legacy)
        legacy_folder = os.path.join("assets", "12_photos")
        if os.path.exists(legacy_folder):
            try:
                files = os.listdir(legacy_folder)
                for f in files:
                    fname_lower = f.lower()
                    base_name = os.path.splitext(fname_lower)[0]
                    for key in search_keys:
                        if key and key == base_name:
                            return os.path.abspath(os.path.join(legacy_folder, f))
            except Exception as e:
                logging.warning(f"Error scanning legacy folder: {e}")
                
        return None

    async def _render_html_scene(self, eto_name, text, duration, subtitle_data, theme_override=None, header_text="", period_type="Daily", anim_style="sakura"):
        """
        Renders the Japanese-themed scene using Playwright.
        Captures screenshots at 30 FPS.
        """
        frames_dir = f"assets/temp/frames_{hash(text)}"
        os.makedirs(frames_dir, exist_ok=True)
        
        # Prepare params
        eto_img = self.get_eto_image_path(eto_name, period_type) or ""
        eto_key = self._get_eto_key(eto_name)
        
        # Get style: COLOR_THEME > ETO_STYLES > Fallback
        style = None
        if theme_override:
            theme_lower = theme_override.lower()
            style = COLOR_STYLES.get(theme_lower)
        
        if not style:
            style = ETO_STYLES.get(eto_key)
             
        if not style:
            # Japanese neutral fallback (deep indigo)
            style = {"grad": ("#0a0a1a", "#1a1a3a", "#3a3a6a"), "glow": "#8080ff", "element": "water"}
        
        grad = style["grad"]
        glow = style["glow"]
        element = style["element"]
        
        # Convert local path to file URL for browser
        if eto_img:
            eto_img_url = f"file:///{eto_img.replace(os.sep, '/')}"
        else:
            eto_img_url = ""
            
        # Construct URL with params
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        encoded_header = urllib.parse.quote(header_text)
        
        url = (f"file:///{self.template_path.replace(os.sep, '/')}?text={encoded_text}&header={encoded_header}&img={eto_img_url}"
               f"&c1={grad[0].replace('#', '%23')}&c2={grad[1].replace('#', '%23')}&c3={grad[2].replace('#', '%23')}"
               f"&glow={glow.replace('#', '%23')}&elem={element}&anim={anim_style}")
        
        logging.info(f"   🌸 Launching Playwright ({anim_style.upper()}) for Japanese scene ({duration}s)...")
        
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
            await page.wait_for_selector("#text-container") 
            
            logging.info(f"   📸 Capturing {total_frames} frames...")
            
            for i in range(total_frames):
                current_time = i / fps
                
                # Update Karaoke Highlight
                if subtitle_data:
                    active_idx = -1
                    for idx, sub in enumerate(subtitle_data):
                        end_time = sub.get('end', sub['start'] + sub.get('duration', 0.5))
                        if sub['start'] <= current_time < end_time:
                            active_idx = idx
                            break
                    
                    if active_idx != -1:
                        await page.evaluate(f"window.setWordActive({active_idx})")
                
                # Update Animations (GSAP seek)
                await page.evaluate(f"window.seek({current_time})")
                
                # Capture Frame
                frame_path = os.path.join(frames_dir, f"frame_{i:04d}.png")
                await page.screenshot(path=frame_path, type='png')
                frames.append(frame_path)
            
            await browser.close()
            
        return frames

    def create_scene(self, eto_name: str, text: str, duration: float, subtitle_data: list = None, theme_override: str = None, header_text: str = "", period_type: str = "Daily"):
        """Wrapper to run async render synchronously. Randomizes Japanese animation style."""
        import random
        # Japanese animation styles
        anim_styles = ['sakura', 'ink', 'zen', 'wave']
        chosen_style = random.choice(anim_styles)
        
        try:
            frames = asyncio.run(self._render_html_scene(eto_name, text, duration, subtitle_data, theme_override, header_text, period_type, chosen_style))
            
            if not frames:
                raise Exception("No frames captured")
                
            clip = ImageSequenceClip(frames, fps=30)
            return clip
            
        except Exception as e:
            logging.error(f"❌ Playwright Render Error: {e}")
            return None

    def get_background_music(self, eto_name: str, mood: str = "zen") -> str:
        """
        Finds appropriate Japanese background music based on Eto and mood.
        Searches in: assets/music/eto/{eto_name}/ or assets/music/mood/{mood}/
        """
        import random
        eto_key = self._get_eto_key(eto_name)
        
        # Search paths in priority order
        search_paths = [
            f"assets/music/eto/{eto_key}",          # Eto-specific music
            f"assets/music/mood/{mood}",             # Mood-based music
            f"assets/music/{mood}",                  # Legacy mood folder
            "assets/music/zen",                      # Fallback to zen
            "assets/music",                          # Root music folder
        ]
        
        for path in search_paths:
            if os.path.exists(path) and os.path.isdir(path):
                try:
                    files = [f for f in os.listdir(path) if f.endswith(('.mp3', '.wav', '.m4a'))]
                    if files:
                        chosen = random.choice(files)
                        full_path = os.path.join(path, chosen)
                        logging.info(f"   🎵 Selected music: {chosen}")
                        return os.path.abspath(full_path)
                except Exception as e:
                    logging.warning(f"Error reading music folder {path}: {e}")
        
        logging.warning("   ⚠️ No background music found. Proceeding without music.")
        return None

    def assemble_final(self, scenes: list, output_path: str, mood: str = "zen", eto_name: str = None):
        """Assembles all scenes with optional Japanese background music."""
        if not scenes:
            logging.error("No scenes to assemble!")
            return
            
        scenes = [s for s in scenes if s is not None]
        if not scenes:
            logging.error("All scenes failed to render.")
            return

        logging.info(f"🎬 Assembling {len(scenes)} Japanese scenes...")
        final_video = run_concatenate(scenes) 
        
        # --- STRICT 59 SECOND LIMIT ---
        MAX_DURATION = 59.0
        if final_video.duration > MAX_DURATION:
            logging.warning(f"⚠️ Video duration {final_video.duration}s exceeds {MAX_DURATION}s. Trimming...")
            final_video = final_video.subclip(0, MAX_DURATION)
            final_video = final_video.fadeout(0.2)
        
        # --- ADD BACKGROUND MUSIC ---
        music_path = self.get_background_music(eto_name or "ne", mood)
        if music_path and os.path.exists(music_path):
            try:
                from moviepy.editor import AudioFileClip, CompositeAudioClip
                
                bg_music = AudioFileClip(music_path)
                
                # Loop music if shorter than video
                if bg_music.duration < final_video.duration:
                    loops_needed = int(final_video.duration / bg_music.duration) + 1
                    from moviepy.editor import concatenate_audioclips
                    bg_music = concatenate_audioclips([bg_music] * loops_needed)
                
                # Trim to video length
                bg_music = bg_music.subclip(0, final_video.duration)
                
                # Lower volume (30% of original)
                bg_music = bg_music.volumex(0.3)
                
                # Fade in/out
                bg_music = bg_music.audio_fadein(1.5).audio_fadeout(1.5)
                
                # Mix with existing audio
                if final_video.audio:
                    final_audio = CompositeAudioClip([final_video.audio, bg_music])
                else:
                    final_audio = bg_music
                    
                final_video = final_video.set_audio(final_audio)
                logging.info(f"   🎵 Background music added successfully")
                
            except Exception as e:
                logging.warning(f"⚠️ Could not add background music: {e}")
        
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

def run_concatenate(clips):
    from moviepy.editor import concatenate_videoclips
    return concatenate_videoclips(clips, method="compose")

