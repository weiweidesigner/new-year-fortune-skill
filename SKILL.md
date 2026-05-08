---
name: new-year-fortune
description: 生成 2026 马年新年签运视频。主输出为 MP4，HTML 仅作为视频截图和预览的中间资产。
dependency:
  python:
    - imageio-ffmpeg>=0.5.0
    - requests>=2.28.0
    - imgkit>=1.2.0
    - selenium>=4.0.0
    - webdriver-manager>=4.0.0
    - playwright>=1.40.0
---

# 新年签运视频生成 Skill

## 任务目标

本 Skill 用于根据用户输入的姓名、性别、出生日期、性格、祈愿等信息，生成一条可分享的 **2026 马年新年签运 MP4 视频**。

核心能力包括：

- AI 运势推演
- 新年祈福金榜 HTML 页面生成，作为视频画面素材
- 新春插画背景生成
- TTS 语音解说生成
- 背景音乐混音
- 签运 MP4 视频合成

> 注意：本 Skill 的主输出是 `new_year_blessing_video.mp4`。  
> `new_year_blessing.html` 是中间文件/预览文件，不是最终主结果。

适合在用户提出以下需求时触发：

- “帮我抽一个新年签，并生成视频”
- “生成一个新年祈福视频”
- “根据我的信息推一下 2026 年运势，做成可分享视频”
- “做一个新年签运短视频”

## 文件结构

```text
new-year-fortune/
├── SKILL.md
├── scripts/
│   └── happynewyear.py
└── assets/
    ├── chinese-new-year.mp3
    └── new-year.mp3
```

## 前置准备

### Python 依赖

脚本会尝试自动安装部分缺失依赖，但建议提前安装：

```bash
pip install imageio-ffmpeg requests imgkit selenium webdriver-manager playwright
```

如果使用 Playwright 截图，建议额外执行：

```bash
python -m playwright install chromium
```

### 系统依赖

视频生成需要将 HTML 页面截图。脚本会优先尝试 Playwright，其次回退到 imgkit / Selenium。

推荐安装其中一种：

```bash
# macOS
brew install wkhtmltopdf

# Ubuntu / Debian
apt-get install wkhtmltopdf
```

或安装 Chrome 浏览器，供 Selenium 使用。

### 环境变量

完整生成 MP4 需要配置：

```bash
export ARK_API_KEY="你的 Ark API Key"
export OPEN_SPEECH_X_API_KEY="你的火山 TTS API Key"
```

也可以使用：

```bash
export BYTE_TTS_API_KEY="你的火山 TTS API Key"
```

说明：

- `ARK_API_KEY` 用于 AI 运势推演和插画生成。
- `OPEN_SPEECH_X_API_KEY` / `BYTE_TTS_API_KEY` 用于 TTS 语音生成。
- 如果缺少 TTS Key，无法生成 MP4，脚本会返回失败，并保留 HTML 预览文件。
- 如果缺少 Ark Key，脚本会使用本地兜底签文，但仍需要 TTS Key 才能生成 MP4。

## 标准调用方式

### 生成 MP4 视频，推荐默认方式

```bash
python scripts/happynewyear.py \
  --user-info "我叫李云龙，男，1995年10月1日出生，ESTP，2026年想要平安幸福" \
  --output-dir output
```

主输出：

```text
output/new_year_blessing_video.mp4
```

中间预览文件：

```text
output/new_year_blessing.html
```

### 显式指定只输出视频

```bash
python scripts/happynewyear.py \
  --user-info "我叫张三，女，2000年5月20日出生，求事业顺利" \
  --output-format video \
  --output-dir output
```

### 自定义 MP4 文件名

```bash
python scripts/happynewyear.py \
  --user-info "我叫王五，求健康平安" \
  --output-format video \
  --output-file wangwu_new_year_fortune.mp4 \
  --output-dir output
```

主输出：

```text
output/wangwu_new_year_fortune.mp4
```

### 仅生成 HTML 预览，调试用

```bash
python scripts/happynewyear.py \
  --user-info "我叫赵六，求财运亨通" \
  --output-format html \
  --output-dir output
```

输出：

```text
output/new_year_blessing.html
```

## 参数说明

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--user-info` | 是 | 用户输入的祈愿信息，例如姓名、性别、生日、性格、愿望等 |
| `--api-key` | 否 | Ark API Key。优先级高于环境变量 `ARK_API_KEY` |
| `--music-files` | 否 | 背景音乐文件路径，多个文件用英文逗号分隔 |
| `--output-format` | 否 | 输出格式：`video`、`html`、`both`，默认 `video` |
| `--output-dir` | 否 | 输出目录，默认当前目录 |
| `--output-file` | 否 | 主输出 MP4 文件名或路径，默认 `new_year_blessing_video.mp4` |
| `--html-output-file` | 否 | 中间 HTML 文件名或路径，默认 `new_year_blessing.html` |
| `--seed` | 否 | 抽签随机种子，用于复现同一次签运类型 |

## 输出说明

### 主输出

```text
new_year_blessing_video.mp4
```

用途：最终可分享的新年签运视频，包含：

- 签运画面
- AI 解签语音
- 新年背景音乐

### 中间输出

```text
new_year_blessing.html
```

用途：生成视频前的画面承载页，可用于预览和截图，不作为主结果返回。

## 返回结果

脚本执行完成后会在标准输出中打印 JSON，便于 OpenClaw 读取最终产物路径。

成功生成 MP4 时：

```json
{
  "status": "success",
  "output_type": "mp4",
  "output_path": "/absolute/path/output/new_year_blessing_video.mp4",
  "html_preview_path": "/absolute/path/output/new_year_blessing.html"
}
```

生成失败时：

```json
{
  "status": "failed",
  "output_type": "mp4",
  "error": "missing_tts_audio",
  "html_preview_path": "/absolute/path/output/new_year_blessing.html"
}
```

## 注意事项

- 本 Skill 默认目标是生成 MP4。
- HTML 是视频画面中间件，不是主输出。
- MP4 生成依赖 TTS、截图工具和 ffmpeg。
- 如果截图工具不可用，视频会生成失败。
- 背景音乐默认读取 `assets/chinese-new-year.mp3` 和 `assets/new-year.mp3`。
- 不建议把 API Key 写死在脚本里，推荐使用环境变量传入。
