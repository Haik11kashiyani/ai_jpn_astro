
import asyncio
from editor import EditorEngine

async def test_anims():
    editor = EditorEngine()
    styles = ['premium', 'cine', 'type', 'pop', 'slide']
    print("Testing Animation Styles...")
    
    for style in styles:
        print(f"   - Testing: {style.upper()}...", end="", flush=True)
        try:
            # Render a dummy scene
            frames = await editor._render_html_scene(
                rashi_name="Mesh (Aries)", 
                text=f"Testing {style} animation style", 
                duration=3.0, 
                subtitle_data=None, # Fixed: Assert None
                theme_override=None, 
                header_text="ANIMATION TEST", 
                period_type="Daily",
                anim_style=style
            )
            if frames and len(frames) > 0:
                print(" OK")
            else:
                print(" NO FRAMES")
        except Exception as e:
            print(f" ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_anims())
