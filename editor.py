import os
import logging
import json
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, ColorClip, vfx, concatenate_videoclips, CompositeAudioClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Monkeypatch ANTIALIAS for MoviePy compatibility with Pillow 10+
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

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
    "mesh": ((180, 40, 40), (60, 10, 10)),       # Red/maroon (Aries - fire)
    "aries": ((180, 40, 40), (60, 10, 10)),
    "vrushabh": ((40, 120, 60), (15, 50, 25)),   # Green (Taurus - earth)
    "taurus": ((40, 120, 60), (15, 50, 25)),
    "mithun": ((200, 180, 50), (80, 60, 20)),    # Yellow (Gemini - air)
    "gemini": ((200, 180, 50), (80, 60, 20)),
    "kark": ((60, 80, 140), (20, 30, 60)),       # Blue (Cancer - water)
    "cancer": ((60, 80, 140), (20, 30, 60)),
    "singh": ((200, 100, 30), (80, 40, 10)),     # Orange (Leo - fire)
    "leo": ((200, 100, 30), (80, 40, 10)),
    "kanya": ((100, 140, 80), (40, 60, 30)),     # Olive green (Virgo - earth)
    "virgo": ((100, 140, 80), (40, 60, 30)),
    "tula": ((140, 100, 160), (50, 35, 60)),     # Purple (Libra - air)
    "libra": ((140, 100, 160), (50, 35, 60)),
    "vrushchik": ((100, 30, 40), (40, 10, 15)),  # Dark red (Scorpio - water)
    "scorpio": ((100, 30, 40), (40, 10, 15)),
    "dhanu": ((160, 80, 40), (60, 30, 15)),      # Brown/orange (Sagittarius - fire)
    "sagittarius": ((160, 80, 40), (60, 30, 15)),
    "makar": ((60, 60, 60), (25, 25, 25)),       # Gray (Capricorn - earth)
    "capricorn": ((60, 60, 60), (25, 25, 25)),
    "kumbh": ((40, 100, 160), (15, 40, 60)),     # Blue (Aquarius - air)
    "aquarius": ((40, 100, 160), (15, 40, 60)),
    "meen": ((80, 120, 140), (30, 50, 60)),      # Teal (Pisces - water)
    "pisces": ((80, 120, 140), (30, 50, 60)),
}

class EditorEngine:
    """
    Creates clean, gradient-themed videos with Rashi images and karaoke-style text.
    No external video API required - pure PIL/MoviePy generation.
    """
    
    def __init__(self):
        self.width = 1080
        self.width = 1080
        self.height = 1920
        self.font_path = "assets/fonts/NotoSansDevanagari-Bold.ttf"
        
        # Ensure font exists (Download if missing)
        if not os.path.exists(self.font_path):
            self._download_font()
            
        os.makedirs("assets/temp", exist_ok=True)

    def _download_font(self):
        """Downloads Noto Sans Devanagari font for proper Hindi rendering."""
        url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        os.makedirs("assets/fonts", exist_ok=True)
        logging.info("⬇️ Downloading Hindi Font...")
        try:
            import requests
            r = requests.get(url, allow_redirects=True)
            with open(self.font_path, 'wb') as f:
                f.write(r.content)
            logging.info("✅ Font downloaded.")
        except Exception as e:
            logging.error(f"❌ Font download failed: {e}")
            # Fallback
            self.font_path = "arial.ttf"

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
                return path
        
        logging.warning(f"Rashi image not found for: {rashi_name}")
        return None

    def _create_gradient_image(self, rashi_name: str) -> str:
        """Creates a gradient background image based on Rashi theme."""
        rashi_key = self._get_rashi_key(rashi_name)
        
        colors = RASHI_GRADIENTS.get(rashi_key, ((30, 30, 60), (10, 10, 20)))
        top_color, bottom_color = colors
        
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Create vertical gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        # Add subtle vignette effect
        for i in range(50):
            alpha = int(255 * (1 - i / 50) * 0.3)
            draw.rectangle([i, i, self.width - i, self.height - i], outline=(0, 0, 0, alpha))
        
        path = f"assets/temp/gradient_{rashi_key}.png"
        img.save(path)
        return path

    def _create_rashi_with_shadow(self, rashi_image_path: str) -> str:
        """Creates Rashi image with soft shadow effect."""
        if not rashi_image_path or not os.path.exists(rashi_image_path):
            return None
            
        rashi_img = Image.open(rashi_image_path).convert("RGBA")
        
        # Resize to fit (50% of width)
        target_width = int(self.width * 0.5)
        aspect = rashi_img.height / rashi_img.width
        target_height = int(target_width * aspect)
        
        if target_height > self.height * 0.4:
            target_height = int(self.height * 0.4)
            target_width = int(target_height / aspect)
        
        rashi_img = rashi_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Create shadow
        shadow_offset = 15
        shadow = Image.new('RGBA', (target_width + shadow_offset * 2, target_height + shadow_offset * 2), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([shadow_offset, shadow_offset, target_width + shadow_offset, target_height + shadow_offset], fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Combine
        final = Image.new('RGBA', (target_width + shadow_offset * 2, target_height + shadow_offset * 2), (0, 0, 0, 0))
        final.paste(shadow, (0, 0), shadow)
        final.paste(rashi_img, (shadow_offset, shadow_offset), rashi_img)
        
        path = f"assets/temp/rashi_shadow_{hash(rashi_image_path)}.png"
        final.save(path)
        return path

    def create_scene(self, rashi_name: str, text: str, duration: float, subtitle_data: list = None) -> CompositeVideoClip:
        """
        Creates a scene with:
        - Gradient background themed to Rashi
        - Rashi image centered with shadow
        - Karaoke-style text at bottom
        """
        layers = []
        
        # 1. Gradient Background
        gradient_path = self._create_gradient_image(rashi_name)
        bg_clip = ImageClip(gradient_path).set_duration(duration)
        layers.append(bg_clip)
        
        # 2. Rashi Image with Shadow (centered, upper half)
        rashi_image_path = self.get_rashi_image_path(rashi_name)
        if rashi_image_path:
            shadow_path = self._create_rashi_with_shadow(rashi_image_path)
            if shadow_path:
                rashi_clip = ImageClip(shadow_path).set_duration(duration)
                # Position in upper-center area
                rashi_clip = rashi_clip.set_position(("center", int(self.height * 0.15)))
                layers.append(rashi_clip)
        
        # 3. Karaoke Subtitles (word by word)
        if subtitle_data:
            subtitle_clips = self._create_karaoke_subtitles(subtitle_data, duration)
            layers.extend(subtitle_clips)
        else:
            # Static text fallback
            text_clip = self._create_static_text(text, duration)
            layers.append(text_clip)
        
        final = CompositeVideoClip(layers, size=(self.width, self.height))
        return final

    def _create_karaoke_subtitles(self, subtitle_data: list, total_duration: float) -> list:
        """Creates karaoke-style word-by-word subtitles."""
        clips = []
        
        for sub in subtitle_data:
            word = sub.get('text', '')
            start = sub.get('start', 0)
            dur = sub.get('duration', 0.5)
            
            if not word.strip():
                continue
            
            # Create word image
            img_path = self._render_karaoke_word(word)
            
            clip = ImageClip(img_path).set_start(start).set_duration(dur)
            # Position at bottom area
            clip = clip.set_position(("center", self.height - 350))
            
            # Add fade effect
            clip = clip.crossfadein(0.1).crossfadeout(0.1)
            
            clips.append(clip)
        
        return clips

    def _render_karaoke_word(self, word: str) -> str:
        """Renders a single word for karaoke display - large, glowing, visible."""
        img_w, img_h = 1000, 200
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 90)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), word, font=font)
        text_w = bbox[2] - bbox[0]
        x = (img_w - text_w) // 2
        y = 40
        
        # Draw glow/shadow
        for offset in range(5, 0, -1):
            alpha = int(255 * (1 - offset / 5) * 0.5)
            draw.text((x + offset, y + offset), word, font=font, fill=(0, 0, 0, alpha))
        
        # Draw main text (bright yellow for visibility)
        draw.text((x, y), word, font=font, fill="#FFDD00", stroke_width=3, stroke_fill="#000000")
        
        path = f"assets/temp/karaoke_{hash(word)}.png"
        img.save(path)
        return path

    def _create_static_text(self, text: str, duration: float) -> ImageClip:
        """Creates static text as fallback when no subtitle data."""
        img_w, img_h = self.width - 100, 400
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 150))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 50)
        except:
            font = ImageFont.load_default()
        
        # Word wrap
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < img_w - 80:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text
        y = 30
        for line in lines[:5]:  # Max 5 lines
            draw.text((40, y), line, font=font, fill="#FFFFFF")
            y += 60
        
        path = f"assets/temp/static_{hash(text)}.png"
        img.save(path)
        
        clip = ImageClip(path).set_duration(duration)
        clip = clip.set_position(("center", self.height - 450))
        return clip

    def assemble_final(self, scenes: list, output_path: str, mood: str = "peaceful"):
        """Assembles all scenes and adds background music."""
        if not scenes:
            logging.error("No scenes to assemble!")
            return
            
        logging.info(f"🎬 Assembling {len(scenes)} scenes...")
        final_video = concatenate_videoclips(scenes, method="compose")
        
        # Add background music
        bg_music_path = self._select_music_by_mood(mood)
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                # Loop music if shorter than video
                if bg_music.duration < final_video.duration:
                    bg_music = vfx.loop(bg_music, duration=final_video.duration)
                else:
                    bg_music = bg_music.subclip(0, final_video.duration)
                
                # Volume set to 20% (audible but not overpowering)
                bg_music = bg_music.volumex(0.20)
                
                if final_video.audio:
                    final_audio = CompositeAudioClip([final_video.audio, bg_music])
                    final_video = final_video.set_audio(final_audio)
                else:
                    final_video = final_video.set_audio(bg_music)
                logging.info(f"   🎵 Background music added: {os.path.basename(bg_music_path)}")
            except Exception as e:
                logging.error(f"   ⚠️ Music error: {e}")
        else:
            logging.warning("   ⚠️ No background music found.")
        
        # Write final video
        fps = 24
        logging.info(f"   📹 Rendering to {output_path}...")
        final_video.write_videofile(
            output_path, 
            fps=fps, 
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

    def _ensure_music_assets(self, music_folder):
        """Downloads default royalty-free music if folder is empty."""
        logging.info("⬇️ Downloading default royalty-free music...")
        
        # Direct links to heavy-weight royalty free tracks (Kevin MacLeod / similar)
        tracks = {
            "peaceful_ambient.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Clean%20Soul.mp3",
            "energetic_upbeat.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Life%20of%20Riley.mp3",
            "mysterious_deep.mp3": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Private%20Reflection.mp3"
        }
        
        try:
            import requests
            for filename, url in tracks.items():
                path = os.path.join(music_folder, filename)
                if not os.path.exists(path):
                    logging.info(f"   ⬇️ Fetching {filename}...")
                    r = requests.get(url, timeout=30)
                    with open(path, 'wb') as f:
                        f.write(r.content)
        except Exception as e:
            logging.warning(f"   ⚠️ Could not download music: {e}")
            
        # Filter by mood
        mood_lower = mood.lower()
        matching_music = [f for f in all_music if mood_lower in f.lower()]
        
        # If no strict match, try broad categories
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
