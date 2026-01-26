# 🔮 AI Japanese Eto Fortune Video Studio (干支占いスタジオ)

An autonomous, Industry-Level video production studio for **Japanese Eto (干支) Fortune Telling**.

Generates authentic Japanese astrology content using traditional systems:

- **干支 (Eto)** - 12 Animal Zodiac
- **九星気学 (Kyusei Kigaku)** - Nine Star Ki
- **六曜 (Rokuyo)** - Daily Luck Calendar
- **五行 (Gogyou)** - Five Elements Theory

## 🌸 Features

- **Authentic Japanese Fortune Content** - Uses real Japanese astrology systems
- **Japanese TTS Narration** - Natural female voice (ja-JP-NanamiNeural)
- **Japanese Aesthetic Visuals** - Cherry blossoms, wave patterns, washi paper textures
- **4 Animation Styles** - Sakura, Ink brush, Zen, Wave
- **Viral YouTube SEO** - Dynamic titles with mandatory #shorts
- **Automated Daily/Monthly/Yearly Videos** - GitHub Actions powered

## 👥 The AI Team

| Agent                         | Role                                                             |
| ----------------------------- | ---------------------------------------------------------------- |
| **星野先生 (Hoshino-sensei)** | Astrologer - Writes authentic Eto fortunes using OpenRouter LLMs |
| **Director Agent**            | Visualizes Japanese aesthetic themes                             |
| **Narrator Agent**            | Speaks in natural Japanese using Neural TTS                      |
| **Editor Engine**             | Renders HTML5 animations with Playwright                         |
| **Uploader Agent**            | Handles YouTube uploads with viral metadata                      |

## 📦 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Environment Variables

Create a `.env` file:

```env
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_API_KEY_BACKUP=backup-key-optional
GOOGLE_AI_API_KEY=your-google-ai-key

# YouTube Upload (Optional)
YOUTUBE_CLIENT_ID=your-client-id
YOUTUBE_CLIENT_SECRET=your-client-secret
YOUTUBE_REFRESH_TOKEN=your-refresh-token
```

### 3. Prepare Eto Images

Place 12 animal images in these folders:

- `assets/eto_daily/` - Daily fortune images
- `assets/eto_monthly/` - Monthly fortune images
- `assets/eto_yearly/` - Yearly fortune images

**Filenames:** `ne.png`, `ushi.png`, `tora.png`, `u.png`, `tatsu.png`, `mi.png`, `uma.png`, `hitsuji.png`, `saru.png`, `tori.png`, `inu.png`, `i.png`

## 🚀 Usage

### Generate Daily Fortune Video

```bash
python main.py --eto "Ne (Rat/子)" --type shorts
```

### Generate Monthly/Yearly Fortune

```bash
python main.py --eto "Tatsu (Dragon/辰)" --type detailed
```

### Generate and Upload to YouTube

```bash
python main.py --eto "Tora (Tiger/寅)" --type shorts --upload
```

## 🐾 12 Eto Animals

| Romaji  | Kanji | Animal  | Element |
| ------- | ----- | ------- | ------- |
| Ne      | 子    | Rat     | Water   |
| Ushi    | 丑    | Ox      | Earth   |
| Tora    | 寅    | Tiger   | Wood    |
| U       | 卯    | Rabbit  | Wood    |
| Tatsu   | 辰    | Dragon  | Earth   |
| Mi      | 巳    | Snake   | Fire    |
| Uma     | 午    | Horse   | Fire    |
| Hitsuji | 未    | Sheep   | Earth   |
| Saru    | 申    | Monkey  | Metal   |
| Tori    | 酉    | Rooster | Metal   |
| Inu     | 戌    | Dog     | Earth   |
| I       | 亥    | Boar    | Water   |

## ⚙️ GitHub Actions

This repo runs automatically:

- **Daily**: 4 batches at 5:30, 6:00, 6:30, 7:00 AM JST
- **Monthly**: 1st of each month
- **Yearly**: New Year's Eve

See `.github/workflows/` for configuration.

## 📁 Project Structure

```
ai_jpn_astro/
├── main.py                 # Main orchestrator
├── editor.py               # Video rendering engine
├── agents/
│   ├── astrologer.py       # LLM-powered fortune generation
│   ├── director.py         # Visual theme analysis
│   ├── narrator.py         # Japanese TTS
│   └── uploader.py         # YouTube upload
├── templates/
│   └── scene.html          # Japanese-themed HTML template
├── assets/
│   ├── eto_daily/          # Daily fortune images
│   ├── eto_monthly/        # Monthly fortune images
│   └── eto_yearly/         # Yearly fortune images
└── .github/workflows/      # Automation workflows
```

## 📄 License

This work is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License.

---

Made with 🌸 for Japanese fortune enthusiasts.
