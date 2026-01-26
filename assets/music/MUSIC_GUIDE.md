# Japanese Background Music Guide (BGM設定ガイド)

## Folder Structure

Reorganize your music folder as follows:

```
assets/music/
├── mood/
│   ├── zen/          # 禅 - Calm, meditative (Koto, Shakuhachi)
│   ├── sakura/       # 桜 - Romantic, gentle (Piano, Strings)
│   ├── mystical/     # 神秘的 - Mysterious, spiritual (Ambient, Bells)
│   └── energetic/    # 元気 - Upbeat, positive (Taiko, Shamisen)
├── eto/              # (Optional) Eto-specific music
│   ├── ne/
│   ├── ushi/
│   └── ... (12 folders)
└── readme.txt
```

## Recommended Japanese Music Styles

### 🧘 Zen (禅) - For calm predictions

- **Instruments**: Koto (琴), Shakuhachi (尺八), Ambient pads
- **Mood**: Meditative, peaceful, temple atmosphere
- **Search terms**: "Japanese zen music", "Koto meditation", "Shakuhachi ambient"
- **Royalty-free sources**:
  - Pixabay: "Japanese ambient"
  - YouTube Audio Library: "Zen", "Koto"
  - Epidemic Sound: "Japanese traditional"

### 🌸 Sakura (桜) - For love/romance predictions

- **Instruments**: Piano, Strings, Soft Koto
- **Mood**: Romantic, gentle, spring feeling
- **Search terms**: "Japanese romantic piano", "Cherry blossom music"
- **Royalty-free sources**:
  - Pixabay: "Japanese piano", "Romantic Japanese"
  - Free Music Archive: "Japan ambient"

### ✨ Mystical (神秘的) - For spiritual predictions

- **Instruments**: Temple bells, Binaural beats, Ethereal pads
- **Mood**: Mysterious, fortune-telling, cosmic
- **Search terms**: "Japanese temple bells", "Mysterious Japan", "Fortune telling BGM"
- **Royalty-free sources**:
  - Pixabay: "Mystical ambient", "Temple atmosphere"
  - Uppbeat: "Spiritual"

### 🥁 Energetic (元気) - For positive/exciting predictions

- **Instruments**: Taiko (太鼓), Shamisen (三味線), Festival drums
- **Mood**: Upbeat, celebratory, powerful
- **Search terms**: "Taiko drums", "Japanese festival music", "Shamisen upbeat"
- **Royalty-free sources**:
  - Pixabay: "Taiko", "Japanese drums"
  - Artlist: "Japanese festival"

## Royalty-Free Music Sources

1. **Pixabay Music** (FREE): https://pixabay.com/music/search/japanese/
2. **YouTube Audio Library** (FREE): YouTube Studio → Audio Library
3. **Free Music Archive** (FREE/CC): https://freemusicarchive.org/
4. **Uppbeat** (FREE with attribution): https://uppbeat.io/
5. **Epidemic Sound** (Subscription): https://www.epidemicsound.com/

## How It Works

1. The editor detects the "mood" from the Director Agent
2. Picks a random track from the matching mood folder
3. Loops and trims to fit video duration
4. Mixes at 30% volume under narration
5. Adds fade in/out for smooth transitions

## Quick Setup

1. Delete the old Rashi folders (`Mesh`, `Kanya`, etc.)
2. Create the new structure above
3. Add 2-3 MP3 files per mood category
4. Each file should be 60-180 seconds long

## Example Download (Free from Pixabay)

| Mood      | Suggested Track            |
| --------- | -------------------------- |
| Zen       | "Japanese Koto Meditation" |
| Sakura    | "Japanese Romantic Piano"  |
| Mystical  | "Temple Bell Ambient"      |
| Energetic | "Taiko Festival Drums"     |
