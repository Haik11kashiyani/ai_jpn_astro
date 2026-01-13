
import asyncio
import os
from moviepy.editor import ImageSequenceClip
from editor import EditorEngine

async def generate_samples():
    editor = EditorEngine()
    styles = ['premium', 'cine', 'type', 'pop', 'slide']
    
    print("------------------------------------------------")
    print(" VIDEO SAMPLE GENERATOR")
    print("------------------------------------------------")
    
    for style in styles:
        print(f"   - Generating Sample: {style.upper()}...", end="", flush=True)
        try:
            # 1. Render Frames
            frames = await editor._render_html_scene(
                rashi_name="Mesh (Aries)", 
                text=f"This is a test of the {style.upper()} animation style. It should fade in smoothly.", 
                duration=5.0, 
                subtitle_data=[{'start': 0.0, 'end': 5.0, 'text': f"This is a test of the {style.upper()} animation style. It should fade in smoothly."}],
                theme_override=None, 
                header_text=f"{style.upper()} STYLE", 
                period_type="Daily",
                anim_style=style
            )
            
            if frames and len(frames) > 0:
                # 2. Compile to Video
                output_filename = f"sample_{style}.mp4"
                clip = ImageSequenceClip(frames, fps=30)
                clip.write_videofile(output_filename, codec='libx264', audio=False, logger=None)
                print(f" OK -> {output_filename}")
            else:
                print(" FAIL (No frames)")
                
        except Exception as e:
            print(f" ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(generate_samples())
