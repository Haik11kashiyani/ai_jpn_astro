# 🎨 Japanese Eto Animal Image Generation Guide

## Quick Setup Commands (Run in PowerShell)

### Step 1: Rename Existing Folders

```powershell
cd c:\Users\Hardik\Desktop\yt_jpn_astro\assets

# Rename image folders
Rename-Item "12_photos" "eto_daily"
Rename-Item "monthly_12_photos" "eto_monthly"
Rename-Item "yearly_12_photos" "eto_yearly"

# Create music mood folders
New-Item -ItemType Directory -Force -Path "music\mood\zen", "music\mood\sakura", "music\mood\mystical", "music\mood\energetic"

# Remove old Rashi music folders
Remove-Item -Recurse -Force "music\music"
```

### Step 2: Push to GitHub

```powershell
cd c:\Users\Hardik\Desktop\yt_jpn_astro
git init
git add .
git commit -m "Japanese Eto Fortune Automation"
git branch -M main
git remote add origin https://github.com/Haik11kashiyani/ai_jpn_astro.git
git push -u origin main --force
```

---

## 🐀 Image Generation Prompts (for AI tools like DALL-E, Midjourney, Ideogram)

### Required Files (same names for all 3 folders)

```
ne.png, ushi.png, tora.png, u.png, tatsu.png, mi.png,
uma.png, hitsuji.png, saru.png, tori.png, inu.png, i.png
```

---

## 📁 FOLDER 1: eto_daily (Daily Fortune - Simple Style)

**Base Prompt Template:**

```
Traditional Japanese art style illustration of a [ANIMAL] for the Japanese zodiac (Eto/干支).

Style: Modern Japanese illustration inspired by ukiyo-e, clean lines, elegant
Composition: Centered portrait, perfect for circular crop, facing slightly right
Background: Simple gradient using [ELEMENT COLORS], no complex patterns
Mood: Mystical, fortune-telling, spiritual, friendly
Size: Square aspect ratio (1:1)

DO NOT include: Text, watermarks, western style, realistic, 3D render
```

### 12 Daily Prompts:

**1. ne.png (子/Rat)**

```
Traditional Japanese art style illustration of a cute RAT/MOUSE for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, clean elegant lines.
The rat is sitting calmly, small and clever-looking, perhaps holding a tiny rice grain or gold coin.
Colors: Deep blue and teal tones (water element).
Background: Simple dark blue gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks, NO realistic style.
```

**2. ushi.png (丑/Ox)**

```
Traditional Japanese art style illustration of a strong OX/COW for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e.
The ox stands calm and powerful, patient expression, sturdy posture.
Colors: Brown, gold, and cream earth tones.
Background: Simple warm brown gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**3. tora.png (寅/Tiger)**

```
Traditional Japanese art style illustration of a majestic TIGER for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, bold strokes.
The tiger is powerful but elegant, traditional orange and black stripes.
Colors: Orange, black, forest green accents (wood element).
Background: Simple deep green gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**4. u.png (卯/Rabbit)**

```
Traditional Japanese art style illustration of a gentle WHITE RABBIT for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, soft and elegant.
The rabbit sits peacefully, perhaps with a subtle moon motif nearby.
Colors: Soft pink, white, pale green (wood element).
Background: Simple soft green gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**5. tatsu.png (辰/Dragon)**

```
Traditional Japanese art style illustration of an EASTERN DRAGON for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, majestic and mystical.
Long serpentine dragon coiling gracefully, Chinese/Japanese style (NOT western dragon).
Colors: Gold, green, and jade tones (earth element).
Background: Simple golden-brown gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**6. mi.png (巳/Snake)**

```
Traditional Japanese art style illustration of an elegant SNAKE for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, mysterious and wise.
The snake is coiled gracefully, perhaps around a branch, intelligent eyes.
Colors: Red, orange, gold (fire element).
Background: Simple deep red gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**7. uma.png (午/Horse)**

```
Traditional Japanese art style illustration of a dynamic HORSE for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, energetic yet elegant.
The horse stands proudly or in mid-gallop motion, mane flowing.
Colors: Deep red, orange, warm browns (fire element).
Background: Simple crimson gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**8. hitsuji.png (未/Sheep)**

```
Traditional Japanese art style illustration of a fluffy SHEEP for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, gentle and peaceful.
The sheep is soft and woolly, calm expression, perhaps with small flowers.
Colors: Cream, soft gold, light brown (earth element).
Background: Simple warm cream gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**9. saru.png (申/Monkey)**

```
Traditional Japanese art style illustration of a playful MONKEY for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, clever and curious.
The monkey sits in a thoughtful or playful pose, intelligent expression.
Colors: Silver, white, metallic tones (metal element).
Background: Simple silver-grey gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**10. tori.png (酉/Rooster)**

```
Traditional Japanese art style illustration of a proud ROOSTER for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, confident and colorful.
The rooster stands tall with beautiful feathers, sunrise energy.
Colors: Red, gold, silver accents (metal element).
Background: Simple silver-white gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**11. inu.png (戌/Dog)**

```
Traditional Japanese art style illustration of a loyal DOG (Shiba Inu or Akita) for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, loyal and protective.
The dog sits faithfully, warm eyes, traditional Japanese breed style.
Colors: Tan, cream, gold (earth element).
Background: Simple warm brown gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

**12. i.png (亥/Boar)**

```
Traditional Japanese art style illustration of a strong WILD BOAR for the Japanese zodiac.
Style: Modern Japanese illustration inspired by ukiyo-e, determined and sincere.
The boar is powerful but friendly, perhaps with cherry blossoms.
Colors: Deep blue, teal, dark grey (water element).
Background: Simple dark blue gradient.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

---

## 📁 FOLDER 2: eto_monthly (Monthly Fortune - With Seasonal Elements)

**Add to each prompt above:**

```
Include subtle Japanese seasonal background elements:
- Cherry blossom petals floating
- Moon and stars
- Mountains in distance
- Bamboo or pine trees
More detailed than daily version, mystical atmosphere.
```

Example for **ne.png** (Monthly):

```
Traditional Japanese art style illustration of a RAT for the Japanese zodiac.
Style: Modern Japanese ukiyo-e inspired, elegant and mystical.
The rat sits calmly with rice grain, surrounded by a mystical atmosphere.
Background: Deep blue gradient with subtle moon and stars, floating particles.
Include: Soft moonlight glow, hint of bamboo silhouette.
Colors: Deep blue, teal, silver (water element).
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

---

## 📁 FOLDER 3: eto_yearly (Yearly Fortune - Grand Cosmic Style)

**Add to each prompt above:**

```
Grand, cosmic, premium style with zodiac wheel elements.
Include: Zodiac circle segment, constellation patterns, cosmic energy aura.
Most elaborate and majestic version.
Gold accents and ethereal glow effects.
```

Example for **tatsu.png** (Yearly - Dragon):

```
Grand traditional Japanese art style illustration of a majestic DRAGON for the Japanese zodiac.
Style: Premium Japanese ukiyo-e inspired, imperial and cosmic.
The dragon coils majestically with cosmic energy aura surrounding it.
Background: Deep cosmic gradient with zodiac wheel segment, gold constellation patterns.
Include: Golden ethereal glow, imperial red and gold accents, celestial energy.
Colors: Gold, deep red, jade green (earth element).
Most elaborate and premium feeling.
Square format, centered, suitable for circular crop.
NO text, NO watermarks.
```

---

## 🎵 Music: Download These Free Japanese Tracks

From **Pixabay Music** (free, no attribution needed):

1. **Zen folder**: Search "Japanese zen koto" - download 2-3 calm tracks
2. **Sakura folder**: Search "Japanese romantic piano" - download 2-3 gentle tracks
3. **Mystical folder**: Search "Japanese temple ambient" - download 2-3 mysterious tracks
4. **Energetic folder**: Search "Taiko drums Japan" - download 2-3 upbeat tracks

Place in: `assets/music/mood/{zen|sakura|mystical|energetic}/`

---

## ✅ Checklist

- [ ] Renamed 12_photos → eto_daily
- [ ] Renamed monthly_12_photos → eto_monthly
- [ ] Renamed yearly_12_photos → eto_yearly
- [ ] Generated 12 images for eto_daily
- [ ] Generated 12 images for eto_monthly
- [ ] Generated 12 images for eto_yearly
- [ ] Downloaded zen music (2-3 tracks)
- [ ] Downloaded sakura music (2-3 tracks)
- [ ] Downloaded mystical music (2-3 tracks)
- [ ] Downloaded energetic music (2-3 tracks)
- [ ] Pushed code to GitHub
- [ ] Set up GitHub secrets
