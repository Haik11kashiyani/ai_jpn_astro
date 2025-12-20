import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip, vfx, concatenate_videoclips, CompositeAudioClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Monkeypatch ANTIALIAS for MoviePy compatibility with Pillow 10+
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rashi name to filename mapping
RASHI_IMAGE_MAP = {
    "mesh": "mesh.jpg",
    "aries": "mesh.jpg",
    "vrushabh": "vrushabh.jpg",
    "taurus": "vrushabh.jpg",
    "mithun": "mithun.jpg",
    "gemini": "mithun.jpg",
    "kark": "kark.jpg",
    "cancer": "kark.jpg",
    "singh": "singh.jpg",
    "leo": "singh.jpg",
    "kanya": "kanya.jpg",
    "virgo": "kanya.jpg",
    "tula": "tula.jpg",
    "libra": "tula.jpg",
    "vrushchik": "vrushchik.jpg",
    "scorpio": "vrushchik.jpg",
    "dhanu": "dhanu.jpg",
    "sagittarius": "dhanu.jpg",
    "makar": "makar.jpg",
    "capricorn": "makar.jpg",
    "kumbh": "kumbh.jpg",
    "aquarius": "kumbh.jpg",
    "meen": "meen.jpg",
    "pisces": "meen.jpg",
}

class EditorEngine:
    """
    Compiles the final video using MoviePy.
    """
    
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.font_path = "c:/Windows/Fonts/nirmala.ttf" # Standard Windows Hindi Font
        if not os.path.exists(self.font_path):
             self.font_path = "Arial" 

    def get_rashi_image_path(self, rashi_name: str) -> str:
        """
        Finds the appropriate rashi image from the 12_photos folder.
        """
        # Extract first word and lowercase
        rashi_key = rashi_name.lower().split()[0].split("(")[0].strip()
        
        # Also check inside parenthesis e.g. "Mesh (Aries)" -> check "aries" too
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

    def create_intro_scene(self, rashi_name: str, rashi_image_path: str, duration: float = 3.0) -> CompositeVideoClip:
        """
        Creates a professional intro scene with the Rashi image prominently displayed.
        """
        layers = []
        
        # 1. Dark gradient background
        bg = ColorClip(size=(self.width, self.height), color=(10, 10, 30), duration=duration)
        layers.append(bg)
        
        # 2. Rashi Image (Large, Centered)
        if rashi_image_path and os.path.exists(rashi_image_path):
            rashi_img = Image.open(rashi_image_path)
            
            # Resize to fit nicely (60% of width, maintain aspect ratio)
            target_width = int(self.width * 0.6)
            aspect = rashi_img.height / rashi_img.width
            target_height = int(target_width * aspect)
            
            # Cap height
            if target_height > self.height * 0.5:
                target_height = int(self.height * 0.5)
                target_width = int(target_height / aspect)
            
            rashi_img = rashi_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Save temporarily
            temp_path = "assets/temp/rashi_intro.png"
            os.makedirs("assets/temp", exist_ok=True)
            rashi_img.save(temp_path)
            
            img_clip = ImageClip(temp_path).set_duration(duration)
            # Center horizontally, place in upper-middle
            x_pos = (self.width - target_width) // 2
            y_pos = int(self.height * 0.15)
            img_clip = img_clip.set_position((x_pos, y_pos))
            
            # Add zoom effect
            img_clip = img_clip.resize(lambda t: 1 + 0.05 * t)
            
            layers.append(img_clip)
        
        # 3. Rashi Name Text (Large, Below Image)
        name_img_path = self._generate_intro_title(rashi_name)
        name_clip = ImageClip(name_img_path).set_duration(duration)
        name_clip = name_clip.set_position(("center", int(self.height * 0.72)))
        layers.append(name_clip)
        
        # Composite
        intro = CompositeVideoClip(layers, size=(self.width, self.height))
        intro = intro.crossfadein(0.5).crossfadeout(0.5)
        
        return intro

    def _generate_intro_title(self, rashi_name: str) -> str:
        """Generates large intro title text."""
        img_w, img_h = 1080, 300
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 90)
        except:
            font = ImageFont.load_default()
        
        # Draw text centered with golden color and shadow
        bbox = draw.textbbox((0, 0), rashi_name, font=font)
        text_w = bbox[2] - bbox[0]
        x = (img_w - text_w) // 2
        
        # Shadow
        draw.text((x + 3, 50 + 3), rashi_name, font=font, fill="#333333")
        # Main text
        draw.text((x, 50), rashi_name, font=font, fill="#FFD700", stroke_width=2, stroke_fill="#8B4513")
        
        temp_path = "assets/temp/intro_title.png"
        os.makedirs("assets/temp", exist_ok=True)
        img.save(temp_path)
        return temp_path

    def create_scene(self, video_path: str, text: str, duration: float, subtitle_path: str = None, rashi_image_path: str = None) -> CompositeVideoClip:
        """
        Creates a single scene with video background, Rashi overlay, and LARGE text.
        """
        layers = []
        
        # 1. Background Video
        if video_path and os.path.exists(video_path):
            try:
                clip = VideoFileClip(video_path)
                if clip.duration < duration:
                    clip = vfx.loop(clip, duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            except Exception as e:
                logging.error(f"Error loading video {video_path}: {e}")
                clip = ColorClip(size=(self.width, self.height), color=(20, 20, 30), duration=duration)
        else:
            clip = ColorClip(size=(self.width, self.height), color=(20, 20, 30), duration=duration)

        # Resize to fill vertical screen
        if hasattr(clip, 'h') and clip.h > 0:
            aspect_ratio = clip.w / clip.h
            target_ratio = self.width / self.height
            
            if aspect_ratio > target_ratio:
                new_w = int(self.height * aspect_ratio)
                clip = clip.resize(height=self.height)
                clip = clip.crop(x1=new_w//2 - self.width//2, width=self.width)
            else:
                clip = clip.resize(width=self.width)
                clip = clip.set_position("center")
        
        layers.append(clip)
        
        # 2. Rashi Image Overlay (Smaller, positioned top-right as identity)
        if rashi_image_path and os.path.exists(rashi_image_path):
            rashi_overlay = ImageClip(rashi_image_path).set_duration(duration)
            rashi_overlay = rashi_overlay.resize(height=200) # Small overlay
            rashi_overlay = rashi_overlay.set_position((self.width - 220, 20)) # Top-right
            rashi_overlay = rashi_overlay.set_opacity(0.9)
            layers.append(rashi_overlay)

        # 3. Text Overlay (LARGE subtitles)
        if subtitle_path and os.path.exists(subtitle_path):
            txt_clip = self._generate_subtitle_clip(subtitle_path, duration)
        else:
            txt_img_path = self._generate_text_image(text)
            txt_clip = ImageClip(txt_img_path).set_duration(duration)
            txt_clip = txt_clip.set_position(("center", self.height - 550)) # Position at bottom
        
        layers.append(txt_clip)
        
        # Composite
        final_clip = CompositeVideoClip(layers, size=(self.width, self.height))
        final_clip = final_clip.crossfadein(0.3)
        
        return final_clip
    
    def _generate_subtitle_clip(self, subtitle_path: str, duration: float) -> CompositeVideoClip:
        """Generates dynamic subtitle clips from JSON with LARGE text (no dark background)."""
        import json
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            subs = json.load(f)
            
        text_clips = []
        
        # NO dark background - just text with stroke for visibility
        
        for sub in subs:
            word = sub['text']
            start = sub['start']
            dur = sub['duration']
            
            img_path = self._render_text_pill(word)
            
            clip = ImageClip(img_path).set_start(start).set_duration(dur)
            clip = clip.set_position(("center", self.height - 280))
            text_clips.append(clip)
        
        # Create transparent base
        base = ColorClip(size=(self.width, self.height), color=(0,0,0), duration=duration).set_opacity(0)
        return CompositeVideoClip([base] + text_clips, size=(self.width, self.height))

    def _render_text_pill(self, text: str) -> str:
        """Renders LARGE text snippet to image - for individual subtitle words."""
        img_w, img_h = 1050, 250
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 110) # MUCH LARGER FONT
        except:
            font = ImageFont.load_default()
            
        bbox = draw.textbbox((0,0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (img_w - text_w) // 2
        
        # Yellow text with thick black stroke for visibility
        draw.text((x, 30), text, font=font, fill="#FFFF00", stroke_width=5, stroke_fill="black")
        
        temp_path = f"assets/temp/word_{hash(text)}.png"
        os.makedirs("assets/temp", exist_ok=True)
        img.save(temp_path)
        return temp_path

    def _generate_text_image(self, text: str) -> str:
        """Helper to render Hindi text to image using PIL - LARGE SIZE with stroke (no dark background)."""
        img_w, img_h = 1080, 500 
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))  # Fully transparent
        draw = ImageDraw.Draw(img)
        
        # NO dark background - just text with stroke
        
        try:
            font = ImageFont.truetype(self.font_path, 72) # LARGER FONT SIZE
        except:
            font = ImageFont.load_default()

        # Word wrap
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_str = " ".join(current_line)
            bbox = draw.textbbox((0,0), line_str, font=font)
            if bbox[2] > img_w - 100:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        # Draw lines centered with shadow for better visibility
        y = 60
        for line in lines:
            bbox = draw.textbbox((0,0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (img_w - text_w) // 2
            # Shadow
            draw.text((x+2, y+2), line, font=font, fill="#222222")
            # Main text
            draw.text((x, y), line, font=font, fill="#FFFFFF", stroke_width=2, stroke_fill="#000000")
            y += 95
            
        temp_path = f"assets/temp/text_{hash(text)}.png"
        os.makedirs("assets/temp", exist_ok=True)
        img.save(temp_path)
        return temp_path

    def assemble_final(self, clips: list, output_path: str, watermark_path: str = None):
        """Concatenates prepared clips and adds background music."""
        if not clips:
            return
            
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add Watermark
        if watermark_path and os.path.exists(watermark_path):
             final_video = self.apply_watermark(final_video, watermark_path)
        
        # Add Background Music
        bg_music_path = "assets/music/bg.mp3"
        if os.path.exists(bg_music_path):
            try:
                bg_music = AudioFileClip(bg_music_path)
                if bg_music.duration < final_video.duration:
                    bg_music = vfx.loop(bg_music, duration=final_video.duration)
                else:
                    bg_music = bg_music.subclip(0, final_video.duration)
                
                bg_music = bg_music.volumex(0.15)
                
                if final_video.audio:
                    final_audio = CompositeAudioClip([final_video.audio, bg_music])
                    final_video = final_video.set_audio(final_audio)
                else:
                    final_video = final_video.set_audio(bg_music)
                logging.info("   🎵 Background music added.")
            except Exception as e:
                logging.error(f"   ⚠️ Could not add background music: {e}")
        
        fps = final_video.fps if hasattr(final_video, 'fps') and final_video.fps else 24

        final_video.write_videofile(
            output_path, 
            fps=fps, 
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            preset="medium"
        )

    def apply_watermark(self, video_clip, watermark_path: str):
        """Overlays a watermark image on the video."""
        if not os.path.exists(watermark_path):
            return video_clip
            
        watermark = ImageClip(watermark_path).set_duration(video_clip.duration)
        watermark = watermark.resize(height=150)
        watermark = watermark.set_position((20, 20)).set_opacity(0.8)
        
        return CompositeVideoClip([video_clip, watermark], size=video_clip.size)
