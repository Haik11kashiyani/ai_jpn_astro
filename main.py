import os
import sys
import argparse
import json
import logging
from datetime import datetime

from agents.astrologer import AstrologerAgent
from agents.director import DirectorAgent
from agents.narrator import NarratorAgent
from agents.uploader import YouTubeUploader
from editor import EditorEngine
from moviepy.editor import AudioFileClip

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- HELPER: HINDI DATE FORMATTER ---
def get_hindi_date_str(date_obj):
    months_map = {
        "January": "जनवरी", "February": "फरवरी", "March": "मार्च", "April": "अप्रैल", 
        "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त", 
        "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"
    }
    en_month = date_obj.strftime("%B")
    hi_month = months_map.get(en_month, en_month)
    return f"{date_obj.day} {hi_month} {date_obj.year}"

def get_hindi_month_str(date_obj):
    months_map = {
        "January": "जनवरी", "February": "फरवरी", "March": "मार्च", "April": "अप्रैल", 
        "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त", 
        "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"
    }
    en_month = date_obj.strftime("%B")
    hi_month = months_map.get(en_month, en_month)
    return f"{hi_month} {date_obj.year}"

def produce_video_from_script(agents, rashi, title_suffix, script, date_str, theme_override=None, period_type="Daily", header_text=""):
    """
    Orchestrates the production of a single video from a script.
    Uses gradient Rashi-themed backgrounds with karaoke text (no Pexels API).
    """
    narrator, editor, director = agents['narrator'], agents['editor'], agents['director']
    
    print(f"\n🎬 STARTING PRODUCTION: {title_suffix} ({header_text})...")
    scenes = []
    
    # ... [Rest of logic same as before, until create_scene call] ...
    
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
        # print(f"      🎤 Generating: {section.upper()}...")
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

    # --- PHASE 2: SMART TRIMMING (Target based on type) ---
    if period_type == "Daily":
        TARGET_DURATION = 58.0
    else:
        TARGET_DURATION = 600.0 # 10 mins for Detailed/Remedy/Monthly

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
        clip = editor.create_scene(
            clean_rashi_name, 
            text, 
            duration, 
            subtitle_data=subtitle_data, 
            theme_override=theme_override,
            header_text=header_text,     # Pass New Header
            period_type=period_type      # Pass Period Context for Image Selection
        )
        
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
    parser.add_argument("--type", type=str, default="shorts", choices=["shorts", "detailed"], help="Video Type: shorts (Morning) or detailed (Evening)")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after generation")
    args = parser.parse_args()
    
    # Initialize Agents (No StockFetcher needed anymore!)
    agents = {
        'astrologer': AstrologerAgent(),
        'director': DirectorAgent(),
        'narrator': NarratorAgent(),
        'editor': EditorEngine(),
        'uploader': YouTubeUploader()
    }
    
    today = datetime.now()
    date_str = today.strftime("%d %B %Y")
    month_year = today.strftime("%B %Y")
    year_str = today.strftime("%Y")
    
    # --- Rashi Index for Drip Scheduling ---
    # Support both spellings (vrushabh/vrishabh, vrushchik/vrishchik)
    RASHI_IDX_MAP = {
        "mesh": 1, "aries": 1,
        "vrushabh": 2, "vrishabh": 2, "taurus": 2,
        "mithun": 3, "gemini": 3,
        "kark": 4, "cancer": 4,
        "singh": 5, "leo": 5,
        "kanya": 6, "virgo": 6,
        "tula": 7, "libra": 7,
        "vrushchik": 8, "vrishchik": 8, "scorpio": 8,
        "dhanu": 9, "sagittarius": 9,
        "makar": 10, "capricorn": 10,
        "kumbh": 11, "aquarius": 11,
        "meen": 12, "pisces": 12
    }
    rashi_key_clean = args.rashi.split('(')[0].strip().lower()
    rashi_idx = RASHI_IDX_MAP.get(rashi_key_clean, 1)
        
    print("\n" + "="*60)
    print(f"YT JYOTISH RAHASYA: Automation Engine")
    print(f"   Target: {args.rashi} (Index: {rashi_idx})")
    print(f"   Date: {date_str}")
    print(f"   Type: {args.type.upper()}")
    print("="*60 + "\n")
    
    generated_content = [] # Track what we produced for upload
    
    # ==========================
    # MODE 1: SHORTS (MORNING)
    # ==========================
    if args.type == "shorts":
        try:
            print("🔮 Generating DAILY Horoscope (Shorts)...")
            daily_script = agents['astrologer'].generate_daily_rashifal(args.rashi, date_str)
            
            # EXTRACT LUCKY COLOR FOR THEME
            theme_color = None
            if "lucky_color" in daily_script:
                l_text = str(daily_script["lucky_color"]).lower()
                valid_colors = ["red", "blue", "green", "yellow", "white", "black", "pink", "orange", "purple", "brown", "gold", "silver"]
                for c in valid_colors:
                    if c in l_text:
                        theme_color = c
                        break
            
            hi_date = get_hindi_date_str(today)
            daily_header = f"दैनिक राशिफल: {hi_date}"
            
            suffix = f"Daily_{today.strftime('%Y%m%d')}"
            produce_video_from_script(
                agents, 
                args.rashi, 
                suffix, 
                daily_script, 
                date_str,
                theme_override=theme_color,
                period_type="Daily",
                header_text=daily_header
            )
            
            # Add to list for upload
            r_clean = args.rashi.split()[0]
            path = f"outputs/{r_clean}_{suffix}.mp4"
            generated_content.append({
                "path": path,
                "period": "Daily",
                "date": date_str,
                "script": daily_script
            })
            
        except Exception as e:
            print(f"❌ Daily Video Failed: {e}")
            import traceback
            traceback.print_exc()

    # ==========================
    # MODE 2: DETAILED (EVENING)
    # ==========================
    elif args.type == "detailed":
        detailed_produced = False
        
        # CHECK 1: YEARLY (Priority 1)
        if today.month == 1 and today.day == rashi_idx:
            try:
                print(f"\n🎆 HAPPY NEW YEAR! It is Jan {today.day}! Generating YEARLY Horoscope for {args.rashi}...")
                yearly_script = agents['astrologer'].generate_yearly_forecast(args.rashi, year_str)
                yearly_header = f"वार्षिक राशिफल: {year_str}"
                
                suffix = f"Yearly_{year_str}"
                produce_video_from_script(
                    agents, args.rashi, suffix, yearly_script, year_str,
                    period_type="Yearly", header_text=yearly_header
                )
                
                r_clean = args.rashi.split()[0]
                generated_content.append({
                    "path": f"outputs/{r_clean}_{suffix}.mp4",
                    "period": "Yearly",
                    "date": year_str,
                    "script": yearly_script
                })
                detailed_produced = True
                
            except Exception as e:
                print(f"❌ Yearly Video Failed: {e}")

        # CHECK 2: MONTHLY (Priority 2, only if not Yearly)
        if not detailed_produced and today.day == rashi_idx: 
            try:
                print(f"\n📅 It is Day {today.day}! Generating MONTHLY Horoscope for {args.rashi}...")
                monthly_script = agents['astrologer'].generate_monthly_forecast(args.rashi, month_year)
                hi_month = get_hindi_month_str(today)
                monthly_header = f"मासिक राशिफल: {hi_month}"
                
                suffix = f"Monthly_{today.strftime('%B_%Y')}"
                produce_video_from_script(
                    agents, args.rashi, suffix, monthly_script, month_year,
                    period_type="Monthly", header_text=monthly_header
                )
                
                r_clean = args.rashi.split()[0]
                generated_content.append({
                    "path": f"outputs/{r_clean}_{suffix}.mp4",
                    "period": "Monthly",
                    "date": month_year,
                    "script": monthly_script
                })
                detailed_produced = True
                
            except Exception as e:
                print(f"❌ Monthly Video Failed: {e}")

        # CHECK 3: DAILY REMEDY (Priority 3, Fallback)
        if not detailed_produced:
            try:
                print(f"\n🧘 Generating DAILY REMEDY DEEP DIVE (Evening Special)...")
                remedy_script = agents['astrologer'].generate_daily_remedy_script(args.rashi, date_str)
                hi_date = get_hindi_date_str(today)
                remedy_header = f"आज का महा-उपाय: {hi_date}"
                
                suffix = f"Remedy_{today.strftime('%Y%m%d')}"
                produce_video_from_script(
                    agents, args.rashi, suffix, remedy_script, date_str,
                    period_type="Daily_Remedy", header_text=remedy_header
                )
                
                r_clean = args.rashi.split()[0]
                generated_content.append({
                    "path": f"outputs/{r_clean}_{suffix}.mp4",
                    "period": "Daily_Remedy",
                    "date": date_str,
                    "script": remedy_script
                })
                
            except Exception as e:
                print(f"❌ Remedy Video Failed: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1) # Fail CI

    # --- UPLOAD LOGIC ---
    if args.upload and generated_content:
        uploader = agents['uploader']
        if uploader.service:
            
            # Scheduling Logic (IST)
            # FORCE ALL UPLOADS TO 6:30 AM (User Request)
            import pytz
            from datetime import timedelta
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            
            # Target: 6:30 AM Today
            target_time = now_ist.replace(hour=6, minute=30, second=0, microsecond=0)
            
            # If we are already past 6:30 AM (e.g. running at 3:00 PM), schedule for TOMORROW 6:30 AM
            if now_ist > target_time:
                target_time = target_time + timedelta(days=1)
                
            print(f"   📅 Target Upload Time: {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

            # Convert to UTC for API if target exists
            utc_publish_at = None
            if target_time:
                target_utc = target_time.astimezone(pytz.utc)
                # Ensure we are at least 15 mins before target? YouTube has rules?
                # Actually, simply passing future time works.
                # Remove timezone info for strict isoformat if needed, but isoformat() handles it.
                utc_publish_at = target_utc.replace(tzinfo=None) # naive UTC

            upload_success_count = 0
            upload_failure_count = 0
            
            for item in generated_content:
                path = item["path"]
                if os.path.exists(path):
                    print(f"\n🚀 Initiating Upload for {item['period']}...")
                    try:
                        # OPTIMIZATION: Extract Metadata directly from Script (1 API Call Total)
                        script_data = item['script']
                        meta = script_data.get("metadata", {})
                        
                        # Validate metadata exists
                        if not meta or "title" not in meta:
                            print("⚠️ Metadata missing in script. Using local fallback.")
                            meta = uploader.generate_metadata(args.rashi, item['date'], item['period'])
                        else:
                            print("✅ Using AI-generated metadata from script.")

                    except Exception as e:
                        print(f"⚠️ Metadata extraction failed: {e}. Using fallback.")
                        meta = uploader.generate_metadata(args.rashi, item['date'], item['period'])
                    
                    if "categoryId" not in meta: meta["categoryId"] = "24"
                    
                    # Pass publish_at and CHECK the result!
                    upload_result = uploader.upload_video(path, meta, publish_at=utc_publish_at)
                    if upload_result:
                        upload_success_count += 1
                        print(f"✅ Upload successful for {item['period']}")
                    else:
                        upload_failure_count += 1
                        print(f"❌ Upload FAILED for {item['period']}")
                else:
                    print(f"❌ Video file not found: {path}")
                    upload_failure_count += 1
            
            # Summary and fail CI if any upload failed
            print(f"\n📊 Upload Summary: {upload_success_count} success, {upload_failure_count} failed")
            if upload_failure_count > 0:
                raise Exception(f"YouTube upload failed! {upload_failure_count} video(s) failed to upload.")
        else:
            print("❌ Upload skipped: No Auth.")
            raise Exception("YouTube authentication failed - cannot upload video.")
    
    # Final check: If upload requested but nothing generated/uploaded, invoke failure
    if args.upload and not generated_content:
         print("❌ No content was generated for upload.")
         sys.exit(1)

if __name__ == "__main__":
    main()
