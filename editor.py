import os
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip, ColorClip, vfx, concatenate_videoclips
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Monkeypatch ANTIALIAS for MoviePy compatibility with Pillow 10+
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

    def create_scene(self, video_path: str, text: str, duration: float) -> CompositeVideoClip:
        """
        Creates a single scene with video background and text overlay.
        """
        # 1. Background Video
        if video_path and os.path.exists(video_path):
            try:
                clip = VideoFileClip(video_path)
                # Loop if too short
                if clip.duration < duration:
                    clip = vfx.loop(clip, duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            except Exception as e:
                logging.error(f"Error loading video {video_path}: {e}")
                clip = ColorClip(size=(self.width, self.height), color=(20, 20, 30), duration=duration)
        else:
            # Fallback Color Background
            clip = ColorClip(size=(self.width, self.height), color=(20, 20, 30), duration=duration)

        # Resize to fill vertical screen
        # Calculate aspect ratio
        if clip.h > 0:
            aspect_ratio = clip.w / clip.h
            target_ratio = self.width / self.height
            
            if aspect_ratio > target_ratio:
                # Too wide, crop sides
                new_w = int(self.height * aspect_ratio)
                clip = clip.resize(height=self.height)
                clip = clip.crop(x1=new_w//2 - self.width//2, width=self.width)
            else:
                # Too tall/narrow, resize by width
                clip = clip.resize(width=self.width)
                # Center vertically
                clip = clip.set_position("center")

        # 2. Text Overlay 
        txt_img_path = self._generate_text_image(text)
        txt_clip = ImageClip(txt_img_path).set_duration(duration)
        txt_clip = txt_clip.set_position(("center", "bottom"))
        
        # 3. Composite
        final_clip = CompositeVideoClip([clip, txt_clip], size=(self.width, self.height))
        
        # Add fade in/out to look cinematic
        final_clip = final_clip.crossfadein(0.5)
        
        return final_clip

    def _generate_text_image(self, text: str) -> str:
        """Helper to render Hindi text to image using PIL."""
        img_w, img_h = 1080, 600 # Bottom area
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background box for text with rounded corners look (simulated)
        draw.rectangle([50, 50, img_w-50, img_h-50], fill=(0, 0, 0, 180))
        
        try:
            font = ImageFont.truetype(self.font_path, 55)
        except:
            font = ImageFont.load_default()

        # Simple word wrap
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            line_str = " ".join(current_line)
            bbox = draw.textbbox((0,0), line_str, font=font)
            if bbox[2] > img_w - 150:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        # Draw lines centered
        y = 100
        for line in lines:
            # Measure text width to center exact
            bbox = draw.textbbox((0,0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (img_w - text_w) // 2
            draw.text((x, y), line, font=font, fill="white")
            y += 80
            
        temp_path = f"assets/temp/text_{hash(text)}.png"
        os.makedirs("assets/temp", exist_ok=True)
        img.save(temp_path)
        return temp_path

    def assemble_final(self, clips: list, output_path: str):
        """Concatenates prepared clips."""
        if not clips:
            return
            
        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            preset="medium"
        )
