---
name: new-year-fortune
description: Generate personalized 2026 Chinese New Year fortune cards and videos from user birth/profile/wish details. Use when the user asks for 新年运势, 抽签, 祈福, 马年签文, blessing cards, fortune HTML pages, TTS narration, or a shareable New Year fortune video.
---

# New Year Fortune

Generate a personalized 2026 Horse Year fortune from user details, then produce:

- `new_year_blessing.html`: a red-and-gold blessing card with fortune text and generated image.
- `new_year_blessing_video.mp4`: an optional narrated video with background music.

## Security

Never store provider keys in this skill or in generated repositories.

Require users to provide secrets at install/configuration time or runtime:

- `ARK_API_KEY`: Volcengine Ark API key for fortune text and image generation.
- `OPEN_SPEECH_X_API_KEY`: Volcengine Open Speech TTS key for narration and video audio.

Optional environment overrides:

- `VOLC_ARK_API_KEY`: fallback alias for `ARK_API_KEY`.
- `VOLC_TTS_API_KEY`: fallback alias for `OPEN_SPEECH_X_API_KEY`.
- `ARK_BASE_URL`: defaults to `https://ark.cn-beijing.volces.com/api/v3`.
- `ARK_LLM_MODEL`: defaults to `ep-20260404091506-zrxm2`.
- `ARK_IMAGE_MODEL`: defaults to `ep-20260126165602-j9z59`.
- `OPEN_SPEECH_RESOURCE_ID`: defaults to `volc.service_type.10029`.
- `OPEN_SPEECH_TTS_SPEAKER`: defaults to `zh_female_gaolengyujie_emo_v2_mars_bigtts`.

For GitHub publishing, keep a `.env` file out of the repository. When a user provides an install command with inline `KEY=value` secrets, extract those values and write them to the local `.env` configuration file with `scripts/configure_secrets.py`.

```bash
npx skills add https://github.com/weiweidesigner/new-year-fortune-skill ARK_API_KEY=<ark-key> OPEN_SPEECH_X_API_KEY=<tts-key>
```

After installation, run this from the skill folder to capture the same command into `.env`:

```bash
python scripts/configure_secrets.py 'npx skills add https://github.com/weiweidesigner/new-year-fortune-skill ARK_API_KEY=<ark-key> OPEN_SPEECH_X_API_KEY=<tts-key>'
```

If the installer does not support inline secret arguments, instruct the user to export environment variables before running the script:

```bash
export ARK_API_KEY="<ark-key>"
export OPEN_SPEECH_X_API_KEY="<tts-key>"
```

## Workflow

1. Ask for the user's name, gender, birth date or 八字 details, personality/context, and 2026 wish if missing.
2. If the user's request includes a command like `npx skills add ... ARK_API_KEY=... OPEN_SPEECH_X_API_KEY=...`, run `python scripts/configure_secrets.py '<full command>'` from the skill folder before generating output.
3. Run `scripts/happynewyear.py` from the skill folder.
4. Return the generated HTML path and, when available, the video path.

Use this command shape:

```bash
python scripts/happynewyear.py \
  --user-info "我叫李云龙，男，1995年10月1日出生，ESTP，2026年想要平安幸福" \
  --output-format both
```

Runtime key overrides are supported:

```bash
python scripts/happynewyear.py \
  --user-info "我叫赵六，求财运亨通" \
  --api-key "<ark-key>" \
  --tts-api-key "<tts-key>"
```

## Output Modes

- Use `--output-format html` for the fastest result and no video capture requirement.
- Use `--output-format video` to create only the video workflow artifacts.
- Use `--output-format both` by default for HTML plus video.
- Use `--music-files "music1.mp3,music2.mp3"` to override bundled background music.
- Use `--seed "stable-id"` when a repeatable fortune grade is needed.

## Dependencies

The script can install missing Python packages automatically, but prefer an isolated environment for repeatable runs.

Python packages used by the full workflow:

```bash
python -m pip install imageio-ffmpeg imgkit selenium webdriver-manager playwright
python -m playwright install chromium
```

Video generation needs one HTML capture backend:

- Preferred: `playwright` with Chromium.
- Fallback: `imgkit` plus system `wkhtmltopdf`.
- Fallback: Selenium plus a Chrome browser.

HTML-only output does not require the capture backend.

## Bundled Resources

- `scripts/happynewyear.py`: main generator script.
- `assets/chinese-new-year.mp3` and `assets/new-year.mp3`: default background music pool.

## Failure Handling

- If `ARK_API_KEY` is missing, stop and ask the user to configure it.
- If a full install command with inline secrets is provided, configure `.env` automatically rather than asking the user to paste secrets again.
- If TTS key is missing or TTS fails, still return the HTML output and explain that video generation was skipped.
- If screenshot/video tooling is unavailable, return the HTML output and suggest installing Playwright Chromium or `wkhtmltopdf`.
