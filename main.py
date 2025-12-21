import os
import sys
import argparse
import json
import logging
from datetime import datetime

from agents.astrologer import AstrologerAgent
from agents.director import DirectorAgent
from agents.narrator import NarratorAgent
from editor import EditorEngine
from moviepy.editor import AudioFileClip

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def produce_video_from_script(agents, rashi, title_suffix, script, date_str):
    """
    Orchestrates the production of a single video from a script.
    Uses gradient Rashi-themed backgrounds with karaoke text (no Pexels API).
    """
    narrator, editor, director = agents['narrator'], agents['editor'], agents['director']
    
    print(f"\n🎬 STARTING PRODUCTION: {title_suffix}...")
    scenes = []
    
    # Debug: Show what script format we received
    print(f"   📋 Script type: {type(script).__name__}")
    if isinstance(script, dict):
        print(f"   📋 Script keys: {list(script.keys())}")
    elif isinstance(script, list):
        print(f"   📋 Script has {len(script)} items")
        # Check if it's a list containing a single dict (common LLM behavior)
        if len(script) == 1 and isinstance(script[0], dict):
            print("   ✅ Unwrapping single-item list -> dict")
            script = script[0]
        else:
            # Fallback: Convert list to text if it's multiple items or strings
            script = {"content": " ".join(str(s) for s in script)}
    
    # Use Director to analyze script and get mood for music
    print(f"   🎬 Director analyzing content mood...")
    screenplay = director.create_screenplay(script)
    content_mood = screenplay.get("mood", "peaceful") if isinstance(screenplay, dict) else "peaceful"
    print(f"   🎵 Detected mood: {content_mood}")
    
    # Define order of sections to ensure flow
    priority_order = ["hook", "intro", "love", "career", "money", "health", "remedy", "lucky_color", "lucky_number", "lucky_dates", "lucky_months"]
    
    # Identify relevant sections from script
    active_sections = []
    for section in priority_order + [k for k in script.keys() if k not in priority_order]:
        if section in script and script[section] and len(str(script[section])) >= 5:
            active_sections.append(section)

    print(f"   📋 Processing {len(active_sections)} active sections...")
    
    # --- PHASE 1: GENERATE ALL AUDIO & MEASURE DURATION ---
    section_audios = {} # {section: {path, duration, subtitle_path}}
    total_duration = 0.0
    
    os.makedirs(f"assets/temp/{title_suffix}", exist_ok=True)
    
    for section in active_sections:
        print(f"      🎤 Generating: {section.upper()}...")
        text = str(script[section])
        
        # Validate that text isn't a stringified dict/list (Defensive Check)
        text_stripped = text.strip()
        if (text_stripped.startswith("{") and "}" in text_stripped) or (text_stripped.startswith("[") and "]" in text_stripped):
             print(f"         ⚠️ WARNING: Section '{section}' appears to be a raw object. Skipping to prevent glitch.")
             continue
             
        audio_path = f"assets/temp/{title_suffix}/{section}.mp3"
        subtitle_path = audio_path.replace(".mp3", ".json")
        
        # Only generate if not exists (or always overwrite to be safe? let's overwrite for fresh speed settings)
        narrator.speak(text, audio_path)
        
        if os.path.exists(audio_path):
            try:
                clip = AudioFileClip(audio_path)
                dur = clip.duration + 0.3 # Buffer
                section_audios[section] = {
                    "path": audio_path,
                    "duration": dur,
                    "subtitle_path": subtitle_path,
                    "text": text,
                    "audio_object": clip # Keep open? No, close and reopen later to save memory
                }
                clip.close() # Close file handle
                total_duration += dur
            except Exception as e:
                print(f"         ⚠️ Audio read error for {section}: {e}")
        else:
            print(f"         ⚠️ Generation failed for {section}")

    print(f"   ⏱️  Total Pre-Render Duration: {total_duration:.2f}s")

    # --- PHASE 2: SMART TRIMMING (TARGET < 58s) ---
    TARGET_DURATION = 58.0
    if total_duration > TARGET_DURATION:
        print(f"   ⚠️ Duration {total_duration:.2f}s > {TARGET_DURATION}s. Initiating SMART TRIMMING.")
        
        # Strategy: Drop sections in this order of "least impact"
        # 1. Intro (Generic filler)
        # 2. Health (Usually steady)
        # 3. Lucky Number (Low value standalone)
        # 4. Lucky Color
        # 5. Money (Rarely drop, but if must)
        # NEVER DROP: Hook, Love, Career, Remedy
        
        drop_candidates = ["intro", "health", "lucky_number", "lucky_color", "money"]
        
        for candidate in drop_candidates:
            if total_duration <= TARGET_DURATION:
                break
            
            if candidate in section_audios:
                dropped_dur = section_audios[candidate]["duration"]
                print(f"      ✂️ Dropping '{candidate.upper()}' (-{dropped_dur:.2f}s)")
                del section_audios[candidate] # Remove from map
                # Remove from active_sections list to maintain order
                if candidate in active_sections:
                    active_sections.remove(candidate)
                total_duration -= dropped_dur
                
        print(f"   ✅ New Duration: {total_duration:.2f}s")
    
    # --- PHASE 3: CREATE SCENES ---
    for section in active_sections:
        if section not in section_audios:
            continue # Was dropped or failed
            
        data = section_audios[section]
        audio_path = data["path"]
        duration = data["duration"]
        subtitle_path = data["subtitle_path"]
        text = data["text"]
        
        print(f"\n   📍 Rendering Scene: {section.upper()} ({duration:.1f}s)")
        
        # Load subtitles
        subtitle_data = None
        if os.path.exists(subtitle_path):
            try:
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
            except: pass
            
        # Create Scene
        clip = editor.create_scene(rashi, text, duration, subtitle_data=subtitle_data)
        
        # Attach Audio
        if clip:
            try:
                audio_clip = AudioFileClip(audio_path)
                clip = clip.set_audio(audio_clip)
                scenes.append(clip)
                print(f"      ✅ Scene ready.")
            except Exception as e:
                print(f"      ❌ Audio attach error: {e}")
        else:
             print(f"      ❌ Scene render failed.")
        
    if not scenes:
        print("❌ No scenes created.")
        raise Exception("No scenes created.")

    # Final Assembly
    print(f"\n🎞️ Assembling Final Master: {title_suffix}")
    output_filename = f"outputs/{rashi.split()[0]}_{title_suffix}.mp4"
    os.makedirs("outputs", exist_ok=True)
    
    # Assemble with background music
    editor.assemble_final(scenes, output_filename, mood=content_mood)
    print(f"\n✅ CREATED: {output_filename}")


def main():
    parser = argparse.ArgumentParser(description="AI Video Studio Orchestrator")
    parser.add_argument("--rashi", type=str, default="Mesh (Aries)", help="Target Rashi")
    args = parser.parse_args()
    
    # Initialize Agents (No StockFetcher needed anymore!)
    agents = {
        'astrologer': AstrologerAgent(),
        'director': DirectorAgent(),
        'narrator': NarratorAgent(),
        'editor': EditorEngine()
    }
    
    today = datetime.now()
    date_str = today.strftime("%d %B %Y")
    month_year = today.strftime("%B %Y")
    year_str = today.strftime("%Y")
    
    print("\n" + "="*60)
    print(f"🌟 YT JYOTISH RAHASYA: Automation Engine 🌟")
    print(f"   Target: {args.rashi}")
    print(f"   Date: {date_str}")
    print(f"   Style: Gradient Theme + Karaoke Text")
    print("="*60 + "\n")
    
    # --- 1. DAILY VIDEO (Always Run) ---
    daily_success = False
    try:
        print("🔮 Generating DAILY Horoscope...")
        daily_script = agents['astrologer'].generate_daily_rashifal(args.rashi, date_str)
        produce_video_from_script(
            agents, 
            args.rashi, 
            f"Daily_{today.strftime('%Y%m%d')}", 
            daily_script, 
            date_str
        )
        daily_success = True
    except Exception as e:
        print(f"❌ Daily Video Failed: {e}")
        import traceback
        traceback.print_exc()

    # --- 2. MONTHLY VIDEO (Run on 1st of Month) ---
    if today.day == 1: 
        try:
            print(f"\n📅 It is the 1st! Generating MONTHLY Horoscope for {month_year}...")
            monthly_script = agents['astrologer'].generate_monthly_forecast(args.rashi, month_year)
            produce_video_from_script(
                agents,
                args.rashi,
                f"Monthly_{today.strftime('%B_%Y')}",
                monthly_script,
                month_year
            )
        except Exception as e:
            print(f"❌ Monthly Video Failed: {e}")

    # --- 3. YEARLY VIDEO (Run on Jan 1st) ---
    if today.day == 1 and today.month == 1:
        try:
            print(f"\n🎆 HAPPY NEW YEAR! Generating YEARLY Horoscope for {year_str}...")
            yearly_script = agents['astrologer'].generate_yearly_forecast(args.rashi, year_str)
            produce_video_from_script(
                agents,
                args.rashi,
                f"Yearly_{year_str}",
                yearly_script,
                year_str
            )
        except Exception as e:
            print(f"❌ Yearly Video Failed: {e}")
            
    # CRITICAL: Exit with error if Daily video failed
    if not daily_success:
        print("\n❌ CRITICAL: Daily Video Production Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
