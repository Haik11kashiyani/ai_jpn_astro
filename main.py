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

def produce_video_from_script(agents, rashi, title_suffix, script, date_str, theme_override=None):
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
    
    
    # Hindi Name Mapping for Pronunciation & Display
    RASHI_HINDI_MAP = {
        "mesh": "मेष", "aries": "मेष",
        "vrushabh": "वृषभ", "taurus": "वृषभ",
        "mithun": "मिथुन", "gemini": "मिथुन",
        "kark": "कर्क", "cancer": "कर्क",
        "singh": "सिंह", "leo": "सिंह",
        "kanya": "कन्या", "virgo": "कन्या",
        "tula": "तुला", "libra": "तुला",
        "vrushchik": "वृश्चिक", "scorpio": "वृश्चिक",
        "dhanu": "धनु", "sagittarius": "धनु",
        "makar": "मकर", "capricorn": "मकर",
        "kumbh": "कुंभ", "aquarius": "कुंभ",
        "meen": "मीन", "pisces": "मीन"
    }
    
    # Determine current Rashi's Hindi Label
    # rashi input key e.g "Mesh (Aries)" -> "mesh"
    rashi_key = rashi.lower().split('(')[0].strip()
    rashi_hindi = RASHI_HINDI_MAP.get(rashi_key, rashi_key)
    
    for section in active_sections:
        print(f"      🎤 Generating: {section.upper()}...")
        original_text = str(script[section])
        
        # --- LOCALIZATION & CLEANUP ---
        # Initialize separate texts
        speech_text = original_text
        display_text = original_text
        
        # 1. Rashi Name Handling
        # Speech: "मेष" (No brackets)
        # Display: "मेष (Mesh)" (With brackets)
        
        # Replace occurrences in text
        # Speech: "मेष" (No English, No Brackets)
        speech_text = speech_text.replace(rashi_key.capitalize(), rashi_hindi)
        speech_text = speech_text.replace(rashi_key.upper(), rashi_hindi)
        # Handle "Mesh" vs "Aries" if mixed
        if rashi_key != rashi_hindi: # If not already same
             speech_text = speech_text.replace("Mesh", "मेष").replace("Aries", "मेष")
        
        # Remove any lingering brackets/English from speech if commonly found
        speech_text = speech_text.replace(f"({rashi_key.capitalize()})", "").replace("()", "")

        # Display: "मेष (Mesh)" (With Brackets for Title/Context)
        # We replace the Hindi name back to "Hindi (English)" format for display if it was replaced
        # OR we just replace English -> "Hindi (English)" direclty
        target_display = f"{rashi_hindi} ({rashi_key.capitalize()})"
        
        if rashi_key.capitalize() in display_text:
             display_text = display_text.replace(rashi_key.capitalize(), target_display)
        elif "Mesh" in display_text:
             display_text = display_text.replace("Mesh", target_display)
             
        # 2. COLOR & NUMBER Localization
        if section == "lucky_color":
            # Map common colors
            colors_map = {
                "Red": "लाल", "Blue": "नीला", "Green": "हरा", "Yellow": "पीला", 
                "White": "सफेद", "Black": "काला", "Pink": "गुलाबी", "Orange": "नारंगी",
                "Purple": "बैंगनी", "Brown": "भूरा", "Grey": "स्लेटी", "Gray": "स्लेटी",
                "Gold": "सुनहरा", "Silver": "चांदी"
            }
            # Extract English Color if possible (Simple check)
            found_color_en = ""
            found_color_hi = ""
            for en, hi in colors_map.items():
                if en.lower() in original_text.lower():
                    found_color_en = en
                    found_color_hi = hi
                    break
            
            if found_color_hi:
                # Format: "Aaj ka shubh rang Lal (Red)"
                # Speech: "Aaj ka shubh rang Lal"
                speech_text = f"आज का शुभ रंग {found_color_hi} है।"
                display_text = f"आज का शुभ रंग: {found_color_hi} ({found_color_en})"
            else:
                 # Fallback
                 speech_text = f"आज का शुभ रंग {original_text} है।"
                 display_text = f"शुभ रंग: {original_text}"

        elif section == "lucky_number":
             # Format: "Aaj ka shubh ank [Number]"
             speech_text = f"आज का शुभ अंक {original_text} है।"
             display_text = f"शुभ अंक: {original_text}"

        # 3. Clean up english words if possible (naive replacement)
        speech_text = speech_text.replace("Lucky Color", "शुभ रंग").replace("Lucky Number", "शुभ अंक")
        display_text = display_text.replace("Lucky Color", "शुभ रंग").replace("Lucky Number", "शुभ अंक")
        
        # Validate that text isn't a stringified dict/list (Defensive Check)
        text_stripped = speech_text.strip()
        if (text_stripped.startswith("{") and "}" in text_stripped) or (text_stripped.startswith("[") and "]" in text_stripped):
             print(f"         ⚠️ WARNING: Section '{section}' appears to be a raw object. Skipping to prevent glitch.")
             continue
             
        audio_path = f"assets/temp/{title_suffix}/{section}.mp3"
        subtitle_path = audio_path.replace(".mp3", ".json")
        
        # Only generate if not exists (or always overwrite to be safe? let's overwrite for fresh speed settings)
        narrator.speak(speech_text, audio_path)
        
        if os.path.exists(audio_path):
            try:
                clip = AudioFileClip(audio_path)
                dur = clip.duration + 0.3 # Buffer
                section_audios[section] = {
                    "path": audio_path,
                    "duration": dur,
                    "subtitle_path": subtitle_path,
                    "text": display_text, # STORE DISPLAY TEXT HERE for Editor
                    "audio_object": clip 
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
            
        # Create Scene (Clean Rashi Name for Display)
        # "Mesh (Aries)" -> "Mesh"
        clean_rashi_name = rashi.split('(')[0].strip()
        clip = editor.create_scene(clean_rashi_name, text, duration, subtitle_data=subtitle_data, theme_override=theme_override)
        
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
    
    # --- Rashi Index for Drip Scheduling ---
    # 1=Mesh, 2=Vrushabh, ... 12=Meen
    RASHI_ORDER = ["mesh", "vrushabh", "mithun", "kark", "singh", "kanya", "tula", "vrushchik", "dhanu", "makar", "kumbh", "meen"]
    rashi_key_clean = args.rashi.split('(')[0].strip().lower()
    try:
        rashi_idx = RASHI_ORDER.index(rashi_key_clean) + 1 # 1-based
    except ValueError:
        rashi_idx = 1 # Fallback
        
    print("\n" + "="*60)
    print(f"🌟 YT JYOTISH RAHASYA: Automation Engine 🌟")
    print(f"   Target: {args.rashi} (Index: {rashi_idx})")
    print(f"   Date: {date_str}")
    print(f"   Style: Dynamic Color Theme + Karaoke Text")
    print("="*60 + "\n")
    
    # --- 1. DAILY VIDEO (Always Run) ---
    daily_success = False
    try:
        print("🔮 Generating DAILY Horoscope...")
        daily_script = agents['astrologer'].generate_daily_rashifal(args.rashi, date_str)
        
        # EXTRACT LUCKY COLOR FOR THEME
        # We want the video background to match the Lucky Color of the day!
        theme_color = None
        if "lucky_color" in daily_script:
            l_text = str(daily_script["lucky_color"]).lower()
            # Simple keyword search
            valid_colors = ["red", "blue", "green", "yellow", "white", "black", "pink", "orange", "purple", "brown", "gold", "silver"]
            for c in valid_colors:
                if c in l_text:
                    theme_color = c
                    break
        
        produce_video_from_script(
            agents, 
            args.rashi, 
            f"Daily_{today.strftime('%Y%m%d')}", 
            daily_script, 
            date_str,
            theme_override=theme_color
        )
        daily_success = True
    except Exception as e:
        print(f"❌ Daily Video Failed: {e}")
        import traceback
        traceback.print_exc()

    # --- 2. MONTHLY VIDEO (Drip Schedule: Day X = Rashi X) ---
    # User Request: "1 for one rashi ... next day next rashi"
    if today.day == rashi_idx: 
        try:
            print(f"\n📅 It is Day {today.day}! Generating MONTHLY Horoscope for {args.rashi}...")
            monthly_script = agents['astrologer'].generate_monthly_forecast(args.rashi, month_year)
            produce_video_from_script(
                agents,
                args.rashi,
                f"Monthly_{today.strftime('%B_%Y')}",
                monthly_script,
                month_year
                # No specific color theme for monthly, or use default Rashi theme
            )
        except Exception as e:
            print(f"❌ Monthly Video Failed: {e}")

    # --- 3. YEARLY VIDEO (Drip Schedule: Jan X = Rashi X) ---
    if today.month == 1 and today.day == rashi_idx:
        try:
            print(f"\n🎆 HAPPY NEW YEAR! It is Jan {today.day}! Generating YEARLY Horoscope for {args.rashi}...")
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
