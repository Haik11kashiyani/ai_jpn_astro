import os
import sys
import time
import argparse
import json
import logging
from datetime import datetime
import pytz

from agents.astrologer import AstrologerAgent
from agents.director import DirectorAgent
from agents.narrator import NarratorAgent
from agents.uploader import YouTubeUploader
from editor import EditorEngine
from moviepy.editor import AudioFileClip

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- ETO (干支) ZODIAC MAPPINGS ---
ETO_MAP = {
    "ne": {"kanji": "子", "animal": "Rat", "element": "water", "compat": ["tatsu", "saru"], "incompat": ["uma"]},
    "ushi": {"kanji": "丑", "animal": "Ox", "element": "earth", "compat": ["mi", "tori"], "incompat": ["hitsuji"]},
    "tora": {"kanji": "寅", "animal": "Tiger", "element": "wood", "compat": ["uma", "inu"], "incompat": ["saru"]},
    "u": {"kanji": "卯", "animal": "Rabbit", "element": "wood", "compat": ["hitsuji", "i"], "incompat": ["tori"]},
    "tatsu": {"kanji": "辰", "animal": "Dragon", "element": "earth", "compat": ["ne", "saru"], "incompat": ["inu"]},
    "mi": {"kanji": "巳", "animal": "Snake", "element": "fire", "compat": ["ushi", "tori"], "incompat": ["i"]},
    "uma": {"kanji": "午", "animal": "Horse", "element": "fire", "compat": ["tora", "inu"], "incompat": ["ne"]},
    "hitsuji": {"kanji": "未", "animal": "Sheep", "element": "earth", "compat": ["u", "i"], "incompat": ["ushi"]},
    "saru": {"kanji": "申", "animal": "Monkey", "element": "metal", "compat": ["ne", "tatsu"], "incompat": ["tora"]},
    "tori": {"kanji": "酉", "animal": "Rooster", "element": "metal", "compat": ["ushi", "mi"], "incompat": ["u"]},
    "inu": {"kanji": "戌", "animal": "Dog", "element": "earth", "compat": ["tora", "uma"], "incompat": ["tatsu"]},
    "i": {"kanji": "亥", "animal": "Boar", "element": "water", "compat": ["u", "hitsuji"], "incompat": ["mi"]},
}

# Kyusei (九星気学) Nine Star Ki mapping
KYUSEI_MAP = {
    1: {"name": "一白水星", "element": "water", "direction": "北 (North)"},
    2: {"name": "二黒土星", "element": "earth", "direction": "南西 (Southwest)"},
    3: {"name": "三碧木星", "element": "wood", "direction": "東 (East)"},
    4: {"name": "四緑木星", "element": "wood", "direction": "東南 (Southeast)"},
    5: {"name": "五黄土星", "element": "earth", "direction": "中央 (Center)"},
    6: {"name": "六白金星", "element": "metal", "direction": "北西 (Northwest)"},
    7: {"name": "七赤金星", "element": "metal", "direction": "西 (West)"},
    8: {"name": "八白土星", "element": "earth", "direction": "北東 (Northeast)"},
    9: {"name": "九紫火星", "element": "fire", "direction": "南 (South)"},
}

# Rokuyo (六曜) - Six-day fortune calendar
ROKUYO_DATA = {
    0: {"name": "先勝", "romaji": "Senshou", "meaning": "午前中が吉、急ぐことは吉", "best": "朝の活動", "avoid": "午後の重要事"},
    1: {"name": "友引", "romaji": "Tomobiki", "meaning": "友を引く日、祝事に良い", "best": "お祝い事", "avoid": "葬儀"},
    2: {"name": "先負", "romaji": "Senbu", "meaning": "午後から吉、急ぐと凶", "best": "午後の活動", "avoid": "朝の急ぎ事"},
    3: {"name": "仏滅", "romaji": "Butsumetsu", "meaning": "万事に凶、控えめに", "best": "休息、内省", "avoid": "新規開始"},
    4: {"name": "大安", "romaji": "Taian", "meaning": "万事に大吉、最良の日", "best": "全ての新規事業", "avoid": "なし"},
    5: {"name": "赤口", "romaji": "Shakkou", "meaning": "正午のみ吉、他は凶", "best": "11時〜13時のみ", "avoid": "朝晩の重要事"},
}

def get_rokuyo(date_obj):
    """Calculate Rokuyo (六曜) for any date using traditional lunar approximation."""
    # Traditional formula: (lunar month + lunar day) % 6
    # Simplified: use solar date as approximation
    rokuyo_index = (date_obj.month + date_obj.day) % 6
    return ROKUYO_DATA[rokuyo_index]

def get_japanese_date_str(date_obj):
    """Format date in Japanese style: 2026年1月26日"""
    return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日"

def get_japanese_month_str(date_obj):
    """Format month in Japanese style: 2026年1月"""
    return f"{date_obj.year}年{date_obj.month}月"

def get_japanese_season(date_obj):
    """Get current Japanese season with traditional name."""
    month = date_obj.month
    if month in [3, 4, 5]:
        return "春 (Spring/Haru)"
    elif month in [6, 7, 8]:
        return "夏 (Summer/Natsu)"
    elif month in [9, 10, 11]:
        return "秋 (Autumn/Aki)"
    else:
        return "冬 (Winter/Fuyu)"

def produce_video_from_script(agents, eto, title_suffix, script, date_str, theme_override=None, period_type="Daily", header_text=""):
    """
    Orchestrates the production of a single video from a script.
    Uses Japanese-themed backgrounds with karaoke text.
    """
    narrator, editor, director = agents['narrator'], agents['editor'], agents['director']
    
    print(f"\n🎬 STARTING PRODUCTION: {title_suffix} ({header_text})...")
    scenes = []
    
    # Debug: Show what script format we received
    print(f"   📋 Script type: {type(script).__name__}")
    if isinstance(script, dict):
        print(f"   📋 Script keys: {list(script.keys())}")
    elif isinstance(script, list):
        print(f"   📋 Script has {len(script)} items")
        if len(script) == 1 and isinstance(script[0], dict):
            print("   ✅ Unwrapping single-item list -> dict")
            script = script[0]
        else:
            script = {"content": " ".join(str(s) for s in script)}
    
    # Use Director to analyze script and get mood for music
    print(f"   ⏳ Cooling down (Safety Pause)...")
    time.sleep(5)
    print(f"   🎬 Director analyzing content mood...")
    screenplay = director.create_screenplay(script)
    content_mood = screenplay.get("mood", "zen") if isinstance(screenplay, dict) else "zen"
    print(f"   🎵 Detected mood: {content_mood}")
    
    # Define order of sections
    priority_order = ["hook", "cosmic_context", "love", "career", "money", "health", "lucky_item", "lucky_color", "lucky_direction", "lucky_number", "omamori_advice", "caution"]
    
    # Identify relevant sections from script
    active_sections = []
    for section in priority_order + [k for k in script.keys() if k not in priority_order]:
        if section in script and script[section] and len(str(script[section])) >= 5:
            if section not in ["metadata"]:  # Skip metadata
                active_sections.append(section)

    print(f"   📋 Processing {len(active_sections)} active sections...")
    
    # --- PHASE 1: GENERATE ALL AUDIO & MEASURE DURATION ---
    section_audios = {}
    total_duration = 0.0
    
    os.makedirs(f"assets/temp/{title_suffix}", exist_ok=True)
    
    # Get Eto info
    eto_key = eto.lower().split('(')[0].strip()
    eto_info = ETO_MAP.get(eto_key, {"kanji": eto_key, "animal": eto_key})
    eto_kanji = eto_info["kanji"]
    
    for section in active_sections:
        original_text = str(script[section])
        
        # Initialize texts
        speech_text = original_text
        display_text = original_text
        
        # Section-specific formatting
        if section == "lucky_color":
            speech_text = f"今日のラッキーカラーは{original_text}です。"
            display_text = f"🎨 ラッキーカラー: {original_text}"
        elif section == "lucky_number":
            speech_text = f"今日のラッキーナンバーは{original_text}です。"
            display_text = f"🔢 ラッキーナンバー: {original_text}"
        elif section == "lucky_direction":
            speech_text = f"今日のラッキー方角は{original_text}です。"
            display_text = f"🧭 ラッキー方角: {original_text}"
        elif section == "lucky_item":
            speech_text = f"今日のラッキーアイテムは{original_text}です。"
            display_text = f"🍀 ラッキーアイテム: {original_text}"
        
        # Validate text
        text_stripped = speech_text.strip()
        if (text_stripped.startswith("{") and "}" in text_stripped) or (text_stripped.startswith("[") and "]" in text_stripped):
            print(f"         ⚠️ WARNING: Section '{section}' appears to be raw object. Skipping.")
            continue
             
        audio_path = f"assets/temp/{title_suffix}/{section}.mp3"
        subtitle_path = audio_path.replace(".mp3", ".json")
        
        narrator.speak(speech_text, audio_path)
        
        if os.path.exists(audio_path):
            try:
                clip = AudioFileClip(audio_path)
                dur = clip.duration + 0.3
                section_audios[section] = {
                    "path": audio_path,
                    "duration": dur,
                    "subtitle_path": subtitle_path,
                    "text": display_text,
                    "audio_object": clip 
                }
                clip.close()
                total_duration += dur
            except Exception as e:
                print(f"         ⚠️ Audio read error for {section}: {e}")
        else:
            print(f"         ⚠️ Generation failed for {section}")

    print(f"   ⏱️  Total Pre-Render Duration: {total_duration:.2f}s")

    # --- PHASE 2: SMART TRIMMING & COMPRESSION ---
    if period_type == "Daily":
        TARGET_DURATION = 59.5 # Maximize use of Shorts 60s limit
    else:
        TARGET_DURATION = 600.0

    # STRATEGY 1: COMPRESSION (Reduce Padding)
    if total_duration > TARGET_DURATION:
        print(f"   ⚠️ Duration {total_duration:.2f}s > {TARGET_DURATION}s. Activating COMPRESSION (Padding 0.3s -> 0.1s).")
        total_duration = 0.0
        # Recalculate with tighter padding
        active_sections_copy = list(active_sections) # copy
        for section in active_sections_copy:
            if section in section_audios:
                # Update duration in object
                clip = section_audios[section]["audio_object"]
                # We closed clip before, so we use the stored path to get approx raw duration
                # Actually we can just subtract 0.2s from the previous 0.3s padded duration
                raw_dur = section_audios[section]["duration"] - 0.3
                new_dur = raw_dur + 0.1
                section_audios[section]["duration"] = new_dur
                total_duration += new_dur
        print(f"   📉 Compressed Duration: {total_duration:.2f}s")

    # STRATEGY 2: TRIMMING (Drop Sections)
    if total_duration > TARGET_DURATION:
        print(f"   ⚠️ Duration {total_duration:.2f}s > {TARGET_DURATION}s. Initiating SMART TRIMMING.")
        
        # Expanded drop list to ensure we obey the limit
        drop_candidates = ["cosmic_context", "caution", "lucky_number", "lucky_direction", "omamori_advice", "lucky_item", "lucky_color"]
        
        for candidate in drop_candidates:
            if total_duration <= TARGET_DURATION:
                break
            
            if candidate in section_audios:
                dropped_dur = section_audios[candidate]["duration"]
                print(f"      ✂️ Dropping '{candidate.upper()}' (-{dropped_dur:.2f}s)")
                del section_audios[candidate]
                if candidate in active_sections:
                    active_sections.remove(candidate)
                total_duration -= dropped_dur
                
        print(f"   ✅ New Duration: {total_duration:.2f}s")
    
    # --- PHASE 3: CREATE SCENES ---
    for section in active_sections:
        if section not in section_audios:
            continue
            
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
        clean_eto_name = eto.split('(')[0].strip()
        clip = editor.create_scene(
            clean_eto_name, 
            text, 
            duration, 
            subtitle_data=subtitle_data, 
            theme_override=theme_override,
            header_text=header_text,
            period_type=period_type
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
    output_filename = f"outputs/{eto.split()[0]}_{title_suffix}.mp4"
    os.makedirs("outputs", exist_ok=True)
    
    editor.assemble_final(scenes, output_filename, mood=content_mood)
    print(f"\n✅ CREATED: {output_filename}")


def main():
    parser = argparse.ArgumentParser(description="AI Japanese Eto Fortune Video Studio")
    parser.add_argument("--eto", type=str, default="Ne (Rat/子)", help="Target Eto (e.g., 'Ne (Rat/子)')")
    parser.add_argument("--type", type=str, default="shorts", choices=["shorts", "detailed"], help="Video Type")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after generation")
    args = parser.parse_args()
    
    # Initialize Agents
    agents = {
        'astrologer': AstrologerAgent(),
        'director': DirectorAgent(),
        'narrator': NarratorAgent(),
        'editor': EditorEngine(),
        'uploader': YouTubeUploader()
    }
    
    # Use JST timezone for correct Japanese date
    jst = pytz.timezone('Asia/Tokyo')
    today = datetime.now(jst)
    date_str = get_japanese_date_str(today)
    month_year = get_japanese_month_str(today)
    year_str = str(today.year)
    
    # Get Rokuyo for today
    rokuyo = get_rokuyo(today)
    season = get_japanese_season(today)
    
    # --- Eto Index for Drip Scheduling ---
    ETO_IDX_MAP = {
        "ne": 1, "rat": 1,
        "ushi": 2, "ox": 2,
        "tora": 3, "tiger": 3,
        "u": 4, "rabbit": 4,
        "tatsu": 5, "dragon": 5,
        "mi": 6, "snake": 6,
        "uma": 7, "horse": 7,
        "hitsuji": 8, "sheep": 8,
        "saru": 9, "monkey": 9,
        "tori": 10, "rooster": 10,
        "inu": 11, "dog": 11,
        "i": 12, "boar": 12
    }
    eto_key_clean = args.eto.split('(')[0].strip().lower()
    eto_idx = ETO_IDX_MAP.get(eto_key_clean, 1)
    
    # Get Eto info for display
    eto_info = ETO_MAP.get(eto_key_clean, {"kanji": "子", "animal": "Rat", "element": "water"})
        
    print("\n" + "="*60)
    print(f"🔮 AI 干支占い (Eto Fortune) Video Studio")
    print(f"   Target: {args.eto} ({eto_info['kanji']}年)")
    print(f"   Date: {date_str}")
    print(f"   六曜: {rokuyo['name']} ({rokuyo['romaji']})")
    print(f"   Season: {season}")
    print(f"   Type: {args.type.upper()}")
    print("="*60 + "\n")
    
    # Initialize counters early to prevent UnboundLocalError
    upload_success_count = 0
    upload_failure_count = 0
    
    generated_content = []
    
    # ==========================
    # MODE 1: SHORTS (DAILY)
    # ==========================
    if args.type == "shorts":
        try:
            print("🔮 Generating DAILY Fortune (今日の運勢)...")
            
            # --- DEEP ASTROLOGY: Derive Parameters ---
            print("   🌌 Consulting Deep Astrology Almanac (LLM)...")
            deep_data = agents['astrologer'].derive_daily_parameters(date_str)
            
            if deep_data:
                print("   ✅ Deep Data Retrieved: ", json.dumps(deep_data, ensure_ascii=False)[:100] + "...")
            else:
                print("   ⚠️ Deep Data unavailable. Using standard calculation.")
            
            daily_script = agents['astrologer'].generate_daily_fortune(
                args.eto, 
                date_str, 
                rokuyo, 
                season, 
                eto_info,
                deep_data=deep_data
            )
            
            print("   ⏳ Script generated. Cooling down 5s...")
            time.sleep(5)
            
            # EXTRACT LUCKY COLOR FOR THEME
            theme_color = None
            if "lucky_color" in daily_script:
                l_text = str(daily_script["lucky_color"]).lower()
                color_map = {
                    "赤": "red", "青": "blue", "緑": "green", "黄": "yellow",
                    "白": "white", "黒": "black", "ピンク": "pink", "オレンジ": "orange",
                    "紫": "purple", "茶": "brown", "金": "gold", "銀": "silver"
                }
                for jp, en in color_map.items():
                    if jp in l_text or en in l_text:
                        theme_color = en
                        break
            
            daily_header = f"今日の運勢 {date_str}"
            
            suffix = f"Daily_{today.strftime('%Y%m%d')}"
            produce_video_from_script(
                agents, 
                args.eto, 
                suffix, 
                daily_script, 
                date_str,
                theme_override=theme_color,
                period_type="Daily",
                header_text=daily_header
            )
            
            eto_clean = args.eto.split()[0]
            path = f"outputs/{eto_clean}_{suffix}.mp4"
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
    # MODE 2: DETAILED (MONTHLY/YEARLY)
    # ==========================
    elif args.type == "detailed":
        detailed_produced = False
        
        # CHECK 1: YEARLY (January only, staggered by Eto index)
        if today.month == 1 and today.day == eto_idx:
            try:
                print(f"\n🎆 新年おめでとう！Generating YEARLY Fortune for {args.eto}...")
                yearly_script = agents['astrologer'].generate_yearly_fortune(args.eto, year_str, eto_info)
                yearly_header = f"{year_str}年 年間運勢"
                
                suffix = f"Yearly_{year_str}"
                produce_video_from_script(
                    agents, args.eto, suffix, yearly_script, year_str,
                    period_type="Yearly", header_text=yearly_header
                )
                
                eto_clean = args.eto.split()[0]
                generated_content.append({
                    "path": f"outputs/{eto_clean}_{suffix}.mp4",
                    "period": "Yearly",
                    "date": year_str,
                    "script": yearly_script
                })
                detailed_produced = True
                
                print("   ⏳ Yearly done. Cooling down 20s...")
                time.sleep(20)
                
            except Exception as e:
                print(f"❌ Yearly Video Failed: {e}")

        # CHECK 2: MONTHLY (Staggered by Eto index)
        if not detailed_produced and today.day == eto_idx: 
            try:
                print(f"\n📅 Generating MONTHLY Fortune for {args.eto}...")
                monthly_script = agents['astrologer'].generate_monthly_fortune(args.eto, month_year, eto_info)
                monthly_header = f"{month_year} 月間運勢"
                
                suffix = f"Monthly_{today.strftime('%Y_%m')}"
                produce_video_from_script(
                    agents, args.eto, suffix, monthly_script, month_year,
                    period_type="Monthly", header_text=monthly_header
                )
                
                eto_clean = args.eto.split()[0]
                generated_content.append({
                    "path": f"outputs/{eto_clean}_{suffix}.mp4",
                    "period": "Monthly",
                    "date": month_year,
                    "script": monthly_script
                })
                detailed_produced = True
                
                print("   ⏳ Monthly done. Cooling down 20s...")
                time.sleep(20)
                
            except Exception as e:
                print(f"❌ Monthly Video Failed: {e}")

        # CHECK 3: DAILY ADVICE (Fallback)
        if not detailed_produced:
            try:
                print(f"\n🧘 Generating DAILY ADVICE (開運アドバイス)...")
                advice_script = agents['astrologer'].generate_daily_advice(args.eto, date_str, rokuyo, eto_info)
                advice_header = f"開運アドバイス {date_str}"
                
                suffix = f"Advice_{today.strftime('%Y%m%d')}"
                produce_video_from_script(
                    agents, args.eto, suffix, advice_script, date_str,
                    period_type="Daily_Advice", header_text=advice_header
                )
                
                eto_clean = args.eto.split()[0]
                generated_content.append({
                    "path": f"outputs/{eto_clean}_{suffix}.mp4",
                    "period": "Daily_Advice",
                    "date": date_str,
                    "script": advice_script
                })
                
            except Exception as e:
                print(f"❌ Advice Video Failed: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

    # --- UPLOAD LOGIC ---
    if args.upload and generated_content:
        uploader = agents['uploader']
        if uploader.service:
            
            # Scheduling: 6:00 AM JST
            from datetime import timedelta
            jst = pytz.timezone('Asia/Tokyo')
            now_jst = datetime.now(jst)
            
            # Schedule for 6 AM JST *today* (we run at 2-3 AM)
            target_time = now_jst.replace(hour=6, minute=0, second=0, microsecond=0)
            
            utc_publish_at = None

            # Logic: If we are at least 15 mins before 6 AM, schedule for 6 AM.
            # If we are past that (e.g. manual run at 10 AM), upload IMMEDIATELY.
            # This prevents "Old News" being scheduled for tomorrow.
            if now_jst < (target_time - timedelta(minutes=15)):
                print(f"   📅 Early Run: Scheduling Publish for {target_time.strftime('%Y-%m-%d %H:%M JST')} (in {int((target_time - now_jst).total_seconds() / 60)} mins)")
                target_utc = target_time.astimezone(pytz.utc)
                utc_publish_at = target_utc.replace(tzinfo=None)
            else:
                 print(f"   ⚠️ Late Run (Past 5:45 AM): Uploading IMMEDIATELY (Public) to ensure Today's Fortune is live.")
                 utc_publish_at = None
            
            for item in generated_content:
                path = item["path"]
                if os.path.exists(path):
                    print(f"\n🚀 Initiating Upload for {item['period']}...")
                    try:
                        script_data = item['script']
                        meta = script_data.get("metadata", {})
                        
                        if not meta or "title" not in meta:
                            print("⚠️ Metadata missing in script. Using fallback.")
                            meta = uploader.generate_metadata(args.eto, item['date'], item['period'], eto_info)
                        else:
                            print("✅ Using AI-generated metadata from script.")
                            # Ensure #shorts is in title
                            if "#shorts" not in meta.get("title", "").lower():
                                meta["title"] = meta["title"].rstrip() + " #shorts"

                    except Exception as e:
                        print(f"⚠️ Metadata extraction failed: {e}. Using fallback.")
                        meta = uploader.generate_metadata(args.eto, item['date'], item['period'], eto_info)
                    
                    if "categoryId" not in meta: meta["categoryId"] = "24"
                    
                    # Human Simulation: Random Delay before upload (1 to 5 mins)
                    import random
                    sleep_sec = random.randint(60, 300)
                    print(f"   ⏳ Human simulation: Sleeping {sleep_sec}s before upload...")
                    time.sleep(sleep_sec)
                    
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
            
            print(f"\n📊 Upload Summary: {upload_success_count} success, {upload_failure_count} failed")
        else:
            print("❌ Upload skipped: No Auth.")
            # raise Exception("YouTube authentication failed.") # Removed this line
    
    if args.upload:
        if upload_success_count == 0:
            print("❌ Start Upload failed for all videos.")
            # Do NOT raise exception here, so artifact upload can proceed
            # sys.exit(0) 
        else:
            print(f"✅ Successfully uploaded {upload_success_count} videos.")
    else:
        print("ℹ️ Upload skipped (dry run).")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        
        # DEBUG: Print file system state
        print("\n🔍 DEBUG: File System Check")
        print(f"   📂 CWD: {os.getcwd()}")
        
        if os.path.exists("outputs"):
            print(f"   📂 outputs/: {os.listdir('outputs')}")
        else:
            print(f"   ⚠️ outputs/ directory does not exist")
            
        if os.path.exists("assets/temp"):
            print(f"   📂 assets/temp/: {os.listdir('assets/temp')}")
            
        sys.exit(1) # Fail the build so we see the error in GitHub Actions
