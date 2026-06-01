#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新年祈福脚本（页签动态写诗版 + 交叉动画 + 图片呼吸推进）

✅ 本版修正（按你最新反馈）：
- ✅ 去掉图片区域底部重复的标题条（.vision-label）
- ✅ 只保留上方那个 wish_8 半透明红色覆盖条（显示：XXXX · XXXX）
- ✅ wish_8 覆盖条贴底显示，不再与 vision-label 叠加
- ✅ 图片裁剪从顶部开始：避免人物头部被裁掉（object-position: center top）

其余逻辑（视频/混音/截图/样式结构/依赖等）不动。
"""

import os
import json
import argparse
import sys
import re
import ssl
import time
import base64
import subprocess
import urllib.request
import urllib.error
import random
import uuid

# ==========================================
# 📦 自动依赖安装模块
# ==========================================
def auto_install_dependencies():
    """检测并自动安装缺失的第三方库"""
    required_libs = ["imageio-ffmpeg"]
    optional_libs = ["imgkit", "selenium", "webdriver-manager", "playwright"]

    missing_libs = []
    optional_missing = []

    for lib in required_libs:
        try:
            import_name = lib.replace("-", "_")
            __import__(import_name)
        except ImportError:
            missing_libs.append(lib)

    for lib in optional_libs:
        try:
            import_name = lib.replace("-", "_")
            __import__(import_name)
        except ImportError:
            optional_missing.append(lib)

    if missing_libs:
        try:
            cmd = [
                sys.executable, "-m", "pip", "install",
                *missing_libs,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--quiet",
                "--root-user-action=ignore"
            ]
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except subprocess.CalledProcessError:
            cmd = [
                sys.executable, "-m", "pip", "install",
                *missing_libs,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ]
            subprocess.check_call(cmd)

    if optional_missing:
        try:
            if "imgkit" in optional_missing:
                cmd = [sys.executable, "-m", "pip", "install", "imgkit",
                       "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                       "--quiet", "--root-user-action=ignore"]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif "selenium" in optional_missing and "webdriver-manager" in optional_missing:
                cmd = [sys.executable, "-m", "pip", "install", "selenium", "webdriver-manager",
                       "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                       "--quiet", "--root-user-action=ignore"]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif "playwright" in optional_missing:
                cmd = [sys.executable, "-m", "pip", "install", "playwright",
                       "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                       "--quiet", "--root-user-action=ignore"]
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

auto_install_dependencies()

def load_local_env():
    """Load gitignored .env files without overriding real environment variables."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for path in candidates:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            pass

load_local_env()

# --- 配置区 ---
SKILL_ID = "7599556663498096690"
LLM_MODEL = os.getenv("ARK_LLM_MODEL", "ep-20260404091506-zrxm2")
IMAGE_MODEL = os.getenv("ARK_IMAGE_MODEL", "ep-20260126165602-j9z59")
BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

OPEN_SPEECH_TTS_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
OPEN_SPEECH_RESOURCE_ID = os.getenv("OPEN_SPEECH_RESOURCE_ID", "volc.service_type.10029")
TTS_SPEAKER = os.getenv("OPEN_SPEECH_TTS_SPEAKER", "zh_female_gaolengyujie_emo_v2_mars_bigtts")
# 豆包语音大模型 2.0 / OpenSpeech TTS 模型名，可通过环境变量覆盖。
# 不同账号开通的模型名可能不同；为空时走资源/音色默认模型。
OPEN_SPEECH_TTS_MODEL = os.getenv("OPEN_SPEECH_TTS_MODEL", "")

# 测试用 TTS Key：你要求先直接放在脚本里，后续上线建议改回环境变量。
DEFAULT_OPEN_SPEECH_X_API_KEY = "6ab48559-f7ca-4283-a639-2268df02bebe"

# 默认输出到桌面，避免从 macOS 根目录 / 运行时出现 Read-only file system
OUTPUT_DIR = os.getenv("NEW_YEAR_OUTPUT_DIR", os.path.join(os.path.expanduser("~"), "Desktop"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

VIDEO_OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "new_year_blessing_video.mp4")
HTML_OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "new_year_blessing.html")

# ✅ 截图/视频捕获目标：外层红包红底框（确保红色露出来）
CAPTURE_TARGET_ID = "captureFrame"

_script_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.abspath(os.path.join(_script_dir, "../assets"))
SUPPORTED_MUSIC_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}

def discover_default_music_pool():
    if not os.path.isdir(ASSETS_DIR):
        return []
    return [
        os.path.join(ASSETS_DIR, name)
        for name in sorted(os.listdir(ASSETS_DIR))
        if os.path.splitext(name)[1].lower() in SUPPORTED_MUSIC_EXTENSIONS
    ]

DEFAULT_MUSIC_POOL = discover_default_music_pool()

BGM_VOLUME = 0.18
WRITE_ANIMATION_FPS = int(os.getenv("WRITE_ANIMATION_FPS", "18"))  # 默认 18fps：动画更流畅；想提速可设为 10/12
WRITE_FRAME_EXT = os.getenv("WRITE_FRAME_EXT", "jpg").lower().strip().lstrip(".") or "jpg"
if WRITE_FRAME_EXT == "jpeg":
    WRITE_FRAME_EXT = "jpg"
if WRITE_FRAME_EXT not in {"jpg", "png"}:
    WRITE_FRAME_EXT = "jpg"
WRITE_FRAME_QUALITY = int(os.getenv("WRITE_FRAME_QUALITY", "96"))  # JPG 高质量，减少文字压缩模糊


# =========================
# ✅ 实时书法字幕配置
# =========================
ENABLE_LIVE_SUBTITLES = os.getenv("ENABLE_LIVE_SUBTITLES", "1") != "0"
SUBTITLE_FONT_NAME = os.getenv("SUBTITLE_FONT_NAME", "Kaiti SC")
SUBTITLE_FONT_SIZE = int(os.getenv("SUBTITLE_FONT_SIZE", "30"))

# 单条字幕最多承载的完整语义长度。超过时优先按逗号/分号等自然停顿拆分，不按固定字数硬切。
SUBTITLE_MAX_CHARS = int(os.getenv("SUBTITLE_MAX_CHARS", "24"))

# 单条字幕内部的视觉换行长度。注意：这是同一条字幕内部换行，不会拆成多个时间段，所以不会出现“碎词逐段播放”。
SUBTITLE_WRAP_CHARS = int(os.getenv("SUBTITLE_WRAP_CHARS", "8"))

# 左侧字幕安全区：避免覆盖中间签卡。中间页卡大致位于 x=480~800，因此字幕限制在 x<=455。
SUBTITLE_SAFE_X = int(os.getenv("SUBTITLE_SAFE_X", "225"))
SUBTITLE_SAFE_Y = int(os.getenv("SUBTITLE_SAFE_Y", "360"))
SUBTITLE_SAFE_CLIP = os.getenv("SUBTITLE_SAFE_CLIP", "")  # 已不再使用裁剪，避免画面出现硬切边

# 字幕与音频的整体对齐偏移。TTS 通常开头会有极短停顿，默认 0.35 秒。
SUBTITLE_START_OFFSET = float(os.getenv("SUBTITLE_START_OFFSET", "0.35"))
SUBTITLE_END_PADDING = float(os.getenv("SUBTITLE_END_PADDING", "0.25"))


# =========================
# ✅ 吉凶概率脚本
# =========================
TYPE_WEIGHTS = [
    ("上上大吉", 0.30),
    ("上吉",     0.50),
    ("中吉",     0.15),
    ("小吉",     0.05),
]

def normalize_type(t: str) -> str:
    t = (t or "").strip()
    mapping = {
        "上上大吉": "上上大吉",
        "上吉": "上吉",
        "中吉": "中吉",
        "小吉": "小吉",
    }
    return mapping.get(t, "")

def pick_fortune_type(rng: random.Random) -> str:
    x = rng.random()
    acc = 0.0
    for t, w in TYPE_WEIGHTS:
        acc += float(w)
        if x <= acc:
            return t
    return TYPE_WEIGHTS[-1][0]

def type_style_hint(t: str) -> str:
    t = normalize_type(t)
    if t == "上上大吉":
        return "氛围：大吉祥瑞，光更明亮、金色光晕更饱满，人物状态昂扬自信，画面通透，喜庆但不俗艳。"
    if t == "上吉":
        return "氛围：吉顺渐起，暖光柔和，金红点缀适度，人物从容向前，画面稳定高级。"
    if t == "中吉":
        return "氛围：平稳向好但需自持，光影对比略强，金色收敛，画面更克制，留白更多，暗示谨慎与节奏。"
    if t == "小吉":
        return "氛围：小吉宜守不宜躁，暖光偏内敛，金色更少，画面更安静沉稳，隐含提醒与边界感。"
    return "氛围：吉运温和，整体克制温暖。"

# =========================
# ✅ user_wish -> wish_8 逻辑
# =========================
def escape_html(s: str) -> str:
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def _only_cjk(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fff]", text or ""))

def ensure_wish8(fortune: dict) -> dict:
    if not isinstance(fortune, dict):
        return fortune
    wish8_raw = fortune.get("wish_8") or fortune.get("wish8") or ""
    wish8 = _only_cjk(str(wish8_raw))

    if len(wish8) >= 8:
        fortune["wish_8"] = wish8[:8]
        return fortune

    src = _only_cjk(str(fortune.get("user_wish") or ""))
    if len(src) < 8:
        src = _only_cjk((fortune.get("title") or "") + (fortune.get("user_wish") or ""))

    if len(src) >= 8:
        fortune["wish_8"] = src[:8]
    else:
        pad = "顺遂安康事业精进财稳"
        fortune["wish_8"] = (src + pad)[:8]
    return fortune

def format_wish8_dot(wish8: str) -> str:
    s = _only_cjk(wish8 or "")
    if len(s) < 8:
        s = (s + "顺遂安康事业精进财稳")[:8]
    left = s[:4]
    right = s[4:8]
    return f"{escape_html(left)}&nbsp;<span class='dot'>·</span>&nbsp;{escape_html(right)}"

# --- 核心工具函数 ---
def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def make_request(url, data, api_key, method="POST", timeout=90):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    if method == "POST":
        req = urllib.request.Request(
            url,
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )
    else:
        req = urllib.request.Request(url, headers=headers, method="GET")

    with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def http_post_bytes(url, data, headers, timeout=120):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as resp:
        return resp.read(), (resp.headers.get("Content-Type", "") or "").lower()

def find_image_url(data):
    if isinstance(data, dict):
        for k, v in data.items():
            if (k == "url" or k == "image_url") and isinstance(v, str) and v.startswith("http"):
                return v
            found = find_image_url(v)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_image_url(item)
            if found:
                return found
    return None

def extract_json_from_text(text):
    if not text:
        return None
    cleaned = text.strip().replace("```json", "```").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None

def collect_streaming_audio(raw_text):
    buf = bytearray()
    decoder = json.JSONDecoder()
    s = raw_text.strip()
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break
        if s[i] != "{":
            i += 1
            continue
        try:
            obj, end = decoder.raw_decode(s, i)
            if isinstance(obj, dict):
                d = obj.get("data")
                if isinstance(d, str) and len(d) > 64:
                    try:
                        buf.extend(base64.b64decode(d))
                    except Exception:
                        pass
            i = end
        except Exception:
            i += 1
    return bytes(buf)

# --- 业务逻辑 ---
def get_fortune_content(user_sentence, api_key, forced_type: str):
    forced_type = normalize_type(forced_type) or "上吉"
    system_prompt = f"""
你是一位精通周易、命理与国学断签的老师傅，擅长根据生辰信息与所求之事推演流年运势。

用户会提供：收福人姓名、祝福内容。
请结合这些具体信息，推演运势，并生成一条专属签文。

【重要约束：type 已由系统按概率抽取并锁定】
- 本次锁定的吉凶判断 type = “{forced_type}”
- 你必须让输出 JSON 中的 type 字段 **严格等于** “{forced_type}”
- 并且：签诗与解曰的语气、风险提示强度、趋吉避凶建议，需要与该 type 的“吉凶程度”相匹配

生成要求：
- 必须基于用户的个人信息与所求事项来写，不允许写成通用祝福语
- 内容要有命理推断感、断语感，而不是模板口号
- 语气像签文与断语，不像客服或AI说明
- 诗句贴合用户处境，可以引用古代有名的诗词
- explanation 要具体指出：事业 / 财运 / 所求之事 的走势与提醒
- wish_8 字段必须由两个四字成语组成，用于高度概括用户的「新年所求」。格式为“四字成语 + 四字成语”，概括其愿望方向。不得输出非成语或非四字结构内容。
- 不要出现“模板”“示例”等元说明
- 严格只返回 JSON（不得有任何前后缀文本）

### 输出结构（字段必须完整）：
{{
  "id": "签名编号（中文签式风格，如：第四十二签）",
  "user_name": "收福人姓名",
  "user_wish": "所求之事（改写为更书面表达）",
  "wish_8": "所求的8字总结（严格8个汉字）",
  "type": "{forced_type}",
  "title": "本签标题（四字或六字断语风格）",
  "poem": "四句签诗，用<br>分行，意象明确，与用户情境相关",
  "explanation": "断语式解签，结合八字气势、以及所求事项给出判断与提醒"
}}
"""
    try:
        url = f"{BASE_URL}/chat/completions"
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"我的信息是：{user_sentence}"}
            ]
        }
        result = make_request(url, data, api_key)
        obj = extract_json_from_text(result["choices"][0]["message"]["content"])
        if isinstance(obj, dict):
            obj["type"] = forced_type
        return obj
    except Exception as e:
        print(f"【错误】{e}")
        return None

def download_fallback_image(fortune_data):
    title = (fortune_data.get("title") or "吉").replace("&", "＆")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#B80000"/>
    <stop offset="100%" stop-color="#7E0000"/>
  </linearGradient>
</defs>
<rect width="800" height="400" fill="url(#g)"/>
<rect x="40" y="40" width="720" height="320" rx="26" fill="none" stroke="#D4AF37" stroke-width="10"/>
<text x="400" y="220" font-size="64" fill="#FFD700" text-anchor="middle" font-family="serif">{title}</text>
</svg>"""
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode('utf-8')).decode('utf-8')}"

def generate_image_background(fortune_data, api_key, forced_type: str, user_sentence: str = ""):
    try:
        forced_type = normalize_type(forced_type) or normalize_type(fortune_data.get("type")) or "上吉"
        poem_text = re.sub(r"<[^>]+>", "", fortune_data.get("poem", "")).strip()
        style_hint = type_style_hint(forced_type)

        image_prompt = (
            f"为用户生成一幅个人签运/祝福意象插画，画面必须高度个性化。"
            f"【吉凶等级锁定】：{forced_type}。{style_hint}"
            f"请依据以下信息提炼意象与隐喻并落成画面："
            f"用户原始信息：{user_sentence}；"
            f"签运主题：{fortune_data.get('title','')}；"
            f"用户所求：{fortune_data.get('user_wish','')}；"
            f"签诗意境：{poem_text}；"
            f"解曰要点：{fortune_data.get('explanation','')}。"
            f"画面内容要求：把“用户所求 + 签诗意境 + 解曰判断”转化为可见的场景、人物状态、动作、环境与光影；"
            f"优先表现诗和解曰里的具体意象，例如山水、门庭、云光、书案、旅途、事业场景、家宅、人际、健康、财富或学业等。"
            f"多样性要求：每次应根据用户信息和签文选择不同主体、构图、环境与象征物，不要重复同一套固定素材库。"
            f"生肖/马元素要求：不要默认出现马、奔马、马剪影、生肖马或马年图腾；只有当签诗、解曰或用户所求明确指向马、骑行、奔腾、驿马、旅途等意象时，才可自然融入。"
            f"风格：宫崎骏漫画风格质感 + 东方诗意叙事氛围，温暖治愈，电影感构图与光影。"
            f"配色：根据签文内容和用户所求决定色彩，可使用青绿、晨光、雪色、墨色、暖木色、城市灯火、海天色、暮色等变化；不要默认使用红金新春配色。"
            f"质量：高清、细腻、超精细细节、8k质感。"
            f"限制：无文字、无题字、无水印、无logo、无印章。"
        )
        data = {
            "model": IMAGE_MODEL,
            "prompt": image_prompt,
            "response_format": "url",
            "size": "2K",
            "watermark": True
        }
        result = make_request(f"{BASE_URL}/images/generations", data, api_key)
        image_url = find_image_url(result)

        if not image_url:
            return download_fallback_image(fortune_data)

        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as response:
            return f"data:image/jpeg;base64,{base64.b64encode(response.read()).decode('utf-8')}"
    except Exception:
        return download_fallback_image(fortune_data)

def build_tts_text_from_fortune(fortune_data: dict) -> str:
    """把签诗 + 解曰整理成适合 TTS 的纯文本。"""
    fortune_data = fortune_data if isinstance(fortune_data, dict) else {}
    raw_poem = fortune_data.get("poem", "")
    text_with_newlines = re.sub(r"<br\s*/?>", "\n", str(raw_poem or ""))
    clean_text = re.sub(r"<[^>]+>", "", text_with_newlines)
    lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
    poem_text = ("，".join(lines) + "。") if lines else ""
    explanation = re.sub(r"<br\s*/?>", "，", str(fortune_data.get("explanation", "") or ""))
    explanation = re.sub(r"<[^>]+>", "", explanation).strip()
    return re.sub(r"\s+", " ", f"{poem_text}解曰。{explanation}").strip()


def generate_tts_audio(fortune_data, tts_api_key=None):
    """
    语音合成逻辑已替换为第一个脚本中的 OpenSpeech / 豆包语音大模型 2.0 调用方式。

    支持的环境变量：
    - OPEN_SPEECH_X_API_KEY / VOLC_TTS_API_KEY：TTS x-api-key
    - OPEN_SPEECH_RESOURCE_ID：默认 volc.service_type.10029
    - OPEN_SPEECH_TTS_SPEAKER：音色，如 zh_female_*_bigtts
    - OPEN_SPEECH_TTS_MODEL：豆包语音大模型 2.0 模型名；为空则不传 model 字段
    """
    load_local_env()
    tts_api_key = tts_api_key or os.getenv("OPEN_SPEECH_X_API_KEY") or os.getenv("VOLC_TTS_API_KEY") or DEFAULT_OPEN_SPEECH_X_API_KEY
    resource_id = os.getenv("OPEN_SPEECH_RESOURCE_ID", OPEN_SPEECH_RESOURCE_ID)
    speaker = os.getenv("OPEN_SPEECH_TTS_SPEAKER", TTS_SPEAKER)
    model = os.getenv("OPEN_SPEECH_TTS_MODEL", OPEN_SPEECH_TTS_MODEL)

    if not tts_api_key:
        print("❌ 缺少 OPEN_SPEECH_X_API_KEY 或 VOLC_TTS_API_KEY，无法生成视频")
        return None

    print("时空回声已捕获，正在塑形神谕之声...")
    tts_text = build_tts_text_from_fortune(fortune_data)
    if not tts_text:
        print("❌ TTS 文本为空，无法生成语音")
        return None

    # 参考第一个脚本：统一空白并限制长度，避免过长文本导致 OpenSpeech 拒绝请求。
    # 如需更长旁白，可把 OPEN_SPEECH_TTS_MAX_CHARS 调大，或自行做分段合成。
    max_chars = int(os.getenv("OPEN_SPEECH_TTS_MAX_CHARS", "320"))
    tts_text = re.sub(r"\s+", " ", tts_text).strip()[:max_chars]

    headers = {
        "x-api-key": tts_api_key,
        "X-Api-Key": tts_api_key,
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": uuid.uuid4().hex,
        "Content-Type": "application/json",
    }
    req_params = {
        "text": tts_text,
        "speaker": speaker,
        "audio_params": {"format": "mp3", "sample_rate": 24000},
    }
    if model:
        req_params["model"] = model

    payload = {
        "user": {"uid": "new-year-blessing-local"},
        "namespace": "BidirectionalTTS",
        "req_params": req_params,
    }

    req = urllib.request.Request(
        OPEN_SPEECH_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as response:
            raw = response.read()
            content_type = (response.headers.get("Content-Type", "") or "").lower()
        if "audio" in content_type or "octet" in content_type:
            return raw
        return collect_streaming_audio(raw.decode("utf-8", "ignore")) or None
    except Exception as e:
        print(f"❌ 语音合成失败：{e}")
        return None

def format_poem(poem_text):
    clean = poem_text.replace("<br>", "。").replace("，", "。").replace(",", "。").replace("\n", "。")
    return "".join([f'<div class="poem-line">{line}</div>' for line in clean.split("。") if line.strip()])

# -----------------------
# ✅ HTML 生成（此处修正：去掉 .vision-label，只保留 wish8）
# ✅ 图片裁剪从顶部开始：object-position: center top
# -----------------------
def clean_display_text(text: str) -> str:
    """用于画面展示：去掉标点，只保留自然文字。"""
    text = re.sub(r"<br\s*/?>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[【】\[\]（）()《》<>“”\"'`·•、，。！？；：,.!?;:\n\r\t]+", "", text)
    text = re.sub(r"\s+", "", text)
    return text.strip()

def remove_explanation_label(text: str) -> str:
    """解曰两个字不进入动态书写内容，但保留后面的解读正文。"""
    text = re.sub(r"<br\s*/?>", "\n", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()
    text = re.sub(r"^\s*[【\[]?\s*解\s*曰\s*[】\]]?\s*[：:。,.，、；;]?\s*", "", text)
    return text.strip()

def split_text_by_punctuation(text: str, max_chars=18):
    """
    以逗号、顿号、句号、问号、感叹号、分号、冒号等作为断句信号。
    标点只负责断句，不进入最终画面。
    如果某个分句仍然过长，再按自然长度做兜底切分，但尽量不碎词。
    """
    text = re.sub(r"<br\s*/?>", "。", text or "")
    text = re.sub(r"<[^>]+>", "", text)
    raw_parts = re.split(r"[，,。.!！?？；;：:、\n\r]+", text)
    parts = []
    for part in raw_parts:
        clean = clean_display_text(part)
        if not clean:
            continue
        while len(clean) > max_chars:
            cut = max_chars
            # 尽量在 10~max_chars 范围内切，避免过短碎词
            if len(clean) - cut < 5:
                cut = len(clean)
            parts.append(clean[:cut])
            clean = clean[cut:]
        if clean:
            parts.append(clean)
    return parts

def poem_lines_for_writing(poem_text: str):
    """签诗优先按 <br>/换行/句号拆成完整诗句。"""
    text = re.sub(r"<br\s*/?>", "\n", poem_text or "")
    text = re.sub(r"<[^>]+>", "", text)
    raw_lines = re.split(r"[\n。.!！?？；;]+", text)
    lines = [clean_display_text(x) for x in raw_lines if clean_display_text(x)]
    if not lines:
        lines = split_text_by_punctuation(poem_text, max_chars=14)
    return lines[:6]

# -----------------------
# ✅ HTML 生成：不再做外部字幕，改成页签内容区“动态写诗”
# -----------------------
def save_final_html(data, image_data_uri, has_video=False, video_base64="", filename=None):
    if filename is None:
        filename = HTML_OUTPUT_FILENAME

    data = ensure_wish8(data if isinstance(data, dict) else {})
    wish8_html = format_wish8_dot(data.get("wish_8", ""))

    poem_segments = poem_lines_for_writing(data.get("poem", ""))
    explanation_text = remove_explanation_label(data.get("explanation", ""))
    explanation_segments = split_text_by_punctuation(explanation_text, max_chars=18)

    # 兜底，避免模型偶发返回空内容导致画面空白
    if not poem_segments:
        poem_segments = ["春风入户福星临", "云开月满照前程", "所愿渐成心自定", "门庭长乐岁常新"]
    if not explanation_segments:
        explanation_segments = ["丙午马年气势渐开", "所求之事宜稳中推进", "凡事守正则吉"]

    poem_segments_json = json.dumps(poem_segments, ensure_ascii=False)
    explanation_segments_json = json.dumps(explanation_segments, ensure_ascii=False)
    # 页签正文显示完整解曰内容：保留正常标点，只去掉 HTML 标签与开头的“解曰”提示字
    explanation_full_text = re.sub(r"<br\s*/?>", "\n", explanation_text or "")
    explanation_full_text = re.sub(r"<[^>]+>", "", explanation_full_text)
    explanation_full_text = re.sub(r"\s+", "", explanation_full_text).strip()
    explanation_full_text_json = json.dumps(explanation_full_text, ensure_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026 新年祈福</title>

<style>
* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  padding: 0;
  background: #C00000;
  font-family: 'Noto Serif SC', serif;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}}

.stage {{
  width: 1280px;
  height: 720px;
  background: #2A0505;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
}}

.stage::before {{
  content: "";
  position: absolute;
  inset: -34px;
  background-image: url("{image_data_uri}");
  background-size: cover;
  background-position: center;
  filter: blur(28px);
  transform: scale(1.06);
  opacity: 0.78;
}}

.stage::after {{
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at center, rgba(255,248,230,0.14), rgba(42,5,5,0.18) 38%, rgba(42,5,5,0.54) 100%),
    linear-gradient(90deg, rgba(80,0,0,0.34), rgba(20,0,0,0.08), rgba(80,0,0,0.34));
}}

.container {{
  width: 320px;
  padding: 0;
  position: relative;
  z-index: 1;
}}

.card {{
  background: linear-gradient(180deg,#C00000,#A80000);
  border-radius: 18px;
  padding: 8px;
  box-shadow: 0 18px 42px rgba(70,0,0,0.62);
}}

.card-inner {{
  background: #FFF8E6;
  border-radius: 12px;
  padding: 24px 18px 18px;
  text-align: center;
}}

.fortune-id {{
  color: #666;
  font-size: 0.78em;
  letter-spacing: 1.5px;
  margin-bottom: 6px;
  font-weight: 700;
}}

.fortune-level {{
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 3.25em;
  color: #C00000;
  margin: 0;
}}

.user-signature {{
  font-size: 0.92em;
  margin-top: 4px;
  font-family: 'Ma Shan Zheng', cursive;
}}

.gold-line {{
  width: 170px;
  height: 2px;
  background: #E5B8B8;
  margin: 8px auto 14px;
}}

.vision-window {{
  width: 100%;
  height: 132px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  margin-bottom: 14px;
}}

.vision-window img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  transform-origin: center center;
  transform: scale(var(--imageScale, 1.035)) translateY(var(--imageY, 0px));
  will-change: transform;
}}

.wish8 {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(192,0,0,0.62);
  color: #fff;
  text-align: center;
  font-weight: 800;
  letter-spacing: 1.5px;
  padding: 5px 8px;
  font-size: 11px;
  line-height: 1.15;
  backdrop-filter: blur(1.5px);
  -webkit-backdrop-filter: blur(1.5px);
}}

.wish8 .dot {{
  font-weight: 900;
  opacity: .95;
  font-size: 12px;
}}

.poem-box {{
  background:
    radial-gradient(circle at 50% 38%, rgba(255, 245, 214, .72), rgba(255, 239, 219, .96) 68%),
    #FFEFDB;
  border-radius: 8px;
  padding: 12px 10px;
  border: 1px solid #EBD3C2;
  margin-bottom: 12px;
  min-height: 126px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}}

.poem-write {{
  width: 100%;
  min-height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}}

.poem-write-line {{
  --reveal: 0%;
  --p: 0;
  position: relative;
  font-family: 'Kaiti SC', 'STKaiti', 'KaiTi', 'Songti SC', serif;
  font-size: 22px;
  font-weight: 900;
  line-height: 1.38;
  letter-spacing: 1.4px;
  white-space: nowrap;
  height: 31px;
  width: max-content;
  max-width: 100%;
  color: transparent;
  opacity: 0;
  transform-origin: center center;
  will-change: opacity, clip-path;
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}}

.poem-write-line .line-main {{
  position: relative;
  z-index: 2;
  color: #2A1206;
  text-shadow: 0 .35px 0 rgba(255,255,255,.18);
}}

.poem-write-line .line-glow,
.poem-write-line .speed-shadow,
.poem-write-line .brush-sweep {{
  position: absolute;
  inset: 0;
  pointer-events: none;
}}

.poem-write-line .line-glow {{
  z-index: 1;
  color: rgba(255, 203, 88, .0);
  text-shadow: none;
}}

.poem-write-line .speed-shadow {{
  z-index: 0;
  color: rgba(120, 67, 20, 0);
  transform: translateX(-12px) scale(1.04);
  filter: blur(2px);
}}

/* 效果 A：清爽毛笔逐字写出：无黄色背景、无黄色光晕、无模糊 */
.poem-write-line.effect-weld.waiting .line-main,
.poem-write-line.effect-weld.waiting .line-glow,
.poem-write-line.effect-weld.waiting .speed-shadow {{
  opacity: 0;
}}

.poem-write-line.effect-weld.writing,
.poem-write-line.effect-weld.done {{
  opacity: 1;
}}

.poem-write-line.effect-weld .line-main {{
  clip-path: inset(0 calc(100% - var(--reveal)) 0 0);
  -webkit-clip-path: inset(0 calc(100% - var(--reveal)) 0 0);
}}

/* 不再使用黄色发光层，只保留极淡的墨色厚度，避免画面脏和发黄 */
.poem-write-line.effect-weld .line-glow {{
  opacity: 0;
}}

.poem-write-line.effect-weld .speed-shadow {{
  opacity: 0;
}}

/* 书写笔锋：墨色扫过，不发黄、不发光、不铺背景 */
.poem-write-line.effect-weld .brush-sweep {{
  z-index: 3;
  top: 3px;
  bottom: 4px;
  width: 12px;
  left: calc(var(--reveal) - 6px);
  border-radius: 999px;
  opacity: 0;
  background: linear-gradient(90deg,
    rgba(42, 18, 6, 0) 0%,
    rgba(42, 18, 6, .18) 42%,
    rgba(42, 18, 6, .05) 72%,
    rgba(42, 18, 6, 0) 100%
  );
  filter: none;
  box-shadow: none;
}}

.poem-write-line.effect-weld.writing .brush-sweep {{
  opacity: .72;
}}

.poem-write-line.effect-weld.done .brush-sweep,
.poem-write-line.effect-weld.waiting .brush-sweep {{
  opacity: 0;
}}

/* 效果 B：第 2、4 句整句出现 + 近推远。
   不拆字、不裂字：整句保持完整，只通过横向舒展、字距收紧、轻微推进形成“由外向内归位”的效果。 */
.poem-write-line.effect-push {{
  overflow: visible;
  perspective: 520px;
}}

.poem-write-line.effect-push.waiting .line-main,
.poem-write-line.effect-push.waiting .line-glow,
.poem-write-line.effect-push.waiting .speed-shadow {{
  opacity: 0;
}}

.poem-write-line.effect-push.writing,
.poem-write-line.effect-push.done {{
  opacity: 1;
  filter: none;
  will-change: transform, opacity;
}}

/* 稳定第 2、4 句的容器宽度：避免字距/视觉宽度变化时被 flex 重新居中，产生左右抖动 */
.poem-write-line.effect-push {{
  width: 100%;
  max-width: 100%;
  text-align: center;
  overflow: visible;
  contain: paint;
  opacity: 1;
  transform: translate3d(0, 0, 0);
  transform-origin: center center;
  will-change: opacity;
}}

.poem-write-line.effect-push .line-main,
.poem-write-line.effect-push .speed-shadow {{
  top: 0;
  left: 0;
  line-height: 31px;
}}



.poem-write-line.effect-push .line-main {{
  display: block;
  width: 100%;
  height: 31px;
  line-height: 31px;
  opacity: var(--pushOpacity, 0);
  clip-path: none;
  -webkit-clip-path: none;
  /*
    第 2、4 句：中心点固定，只叠加两个效果：
    1）缩放：由大到小，形成由近到远的感觉；
    2）透明度：由虚到实。
    不做 X/Y 位移、不改字距、不加影子。
    同时固定 height/line-height，避免字体基线在缩放时参与布局重算。
  */
  transform: translate3d(0, 0, 0) scale3d(var(--pushScale, 1), var(--pushScale, 1), 1);
  transform-origin: 50% 50%;
  letter-spacing: 1.4px;
  text-shadow: 0 .35px 0 rgba(255,255,255,.18);
  backface-visibility: hidden;
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}}

.poem-write-line.effect-push .line-glow {{
  opacity: 0;
}}

.poem-write-line.effect-push .speed-shadow {{
  display: none;
  opacity: 0;
}}

.poem-write-line.effect-push .brush-sweep,
.poem-write-line.effect-push.writing .brush-sweep,
.poem-write-line.effect-push.done .brush-sweep,
.poem-write-line.effect-push.waiting .brush-sweep {{
  opacity: 0;
  display: none;
}}

.explanation {{
  min-height: 126px;
  font-size: 0.70em;
  color: #514036;
  line-height: 1.62;
  text-align: justify;
  background: rgba(255, 248, 230, 0.72);
  border-radius: 8px;
  padding: 8px 8px 6px;
  border: 1px solid rgba(235,211,194,0.55);
}}

.explanation-content {{
  opacity: 0;
  transform: translateY(4px);
}}

.explanation-content.visible {{
  opacity: 1;
  transform: translateY(0);
  animation: inkBlockIn .28s ease-out both;
}}

.explanation strong {{
  color: #C00000;
}}

.explanation-write {{
  color: #4B372C;
  font-weight: 500;
  text-shadow: 0 0 5px rgba(212, 175, 55, .10);
}}

.write-caret {{
  display: none;
}}

.footer {{
  margin-top: 10px;
  font-size: 0.68em;
  color: #999;
  opacity: 0;
  transform: translateY(4px);
}}

.footer.visible {{
  opacity: 1;
  transform: translateY(0);
  animation: footerSealIn .42s ease-out both;
}}

@keyframes inkBlockIn {{
  0% {{ opacity: 0; transform: translateY(4px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes footerSealIn {{
  0% {{ opacity: 0; transform: translateY(4px) scale(.98); }}
  100% {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

@media (max-width: 480px) {{
  .stage {{ transform: scale(calc(100vw / 1280)); transform-origin: center center; }}
}}
</style>
</head>

<body>
<div class="stage" id="{CAPTURE_TARGET_ID}">
  <div class="container">
    <div class="card">
      <div class="card-inner">
        <div class="fortune-id">{escape_html(data.get('id',''))}</div>
        <div class="fortune-level">{escape_html(data.get('type',''))}</div>

        <div class="user-signature">收福人：{escape_html(data.get('user_name',''))}</div>
        <div class="gold-line"></div>

        <div class="vision-window">
          <img src="{image_data_uri}">
          <div class="wish8">{wish8_html}</div>
        </div>

        <div class="poem-box">
          <div id="poemWrite" class="poem-write"></div>
        </div>

        <div class="explanation">
          <div id="explanationContent" class="explanation-content">
            <strong>【解曰】</strong><span id="explanationWrite" class="explanation-write"></span>
          </div>
        </div>

        <div id="footerSeal" class="footer">新年签运 · 2026 马年</div>
      </div>
    </div>
  </div>
</div>

<script>
const POEM_SEGMENTS = {poem_segments_json};
const EXPLANATION_SEGMENTS = {explanation_segments_json};
const EXPLANATION_FULL_TEXT = {explanation_full_text_json};
let WRITE_DURATION = 12;
let WRITE_TIMELINE = [];
let EXPLANATION_REVEAL_AT = 999;
let FOOTER_REVEAL_AT = 999;
let POEM_DOM_READY = false;

function charLen(s) {{
  return Array.from(s || '').length;
}}

function buildWritingTimeline(duration) {{
  const safeDuration = Math.max(6, Number(duration || 12));
  const startPad = 0.35;
  const endPad = 0.28;
  const explainPause = 0.72; // 对应语音读“解曰”的时间，画面此时不提前展示解曰内容

  const poemWeight = POEM_SEGMENTS.reduce((sum, t) => sum + Math.max(4, charLen(t)), 0);
  const expWeight = EXPLANATION_SEGMENTS.reduce((sum, t) => sum + Math.max(4, charLen(t)), 0);
  const totalWeight = Math.max(1, poemWeight + expWeight);

  const usable = Math.max(4, safeDuration - startPad - endPad - explainPause);
  const poemTotalDuration = usable * poemWeight / totalWeight;
  const expTotalDuration = usable * expWeight / totalWeight;

  const minPoemSlot = 0.72;
  const timeline = [];
  let cursor = startPad;

  const poemTotalWeight = Math.max(1, poemWeight);
  POEM_SEGMENTS.forEach((text, index) => {{
    const weight = Math.max(4, charLen(text));
    const dur = Math.max(minPoemSlot, poemTotalDuration * weight / poemTotalWeight);
    timeline.push({{
      target: 'poem',
      index,
      text,
      start: cursor,
      end: cursor + dur
    }});
    cursor += dur;
  }});

  let revealAt = cursor + explainPause;
  const maxRevealAt = Math.max(startPad + 0.5, safeDuration - endPad - Math.max(1.2, expTotalDuration));
  revealAt = Math.min(revealAt, maxRevealAt);

  // 如果诗句因为最小时长挤压了整体时间，就整体压缩诗句时间轴，确保解曰不会晚到音频末尾才出现。
  if (timeline.length && timeline[timeline.length - 1].end + explainPause > revealAt) {{
    const lastEnd = timeline[timeline.length - 1].end;
    const targetPoemEnd = Math.max(startPad + 0.5, revealAt - explainPause);
    const scale = (targetPoemEnd - startPad) / Math.max(0.1, lastEnd - startPad);
    timeline.forEach(item => {{
      item.start = startPad + (item.start - startPad) * scale;
      item.end = startPad + (item.end - startPad) * scale;
    }});
  }}

  EXPLANATION_REVEAL_AT = revealAt;
  // 底部“新年签运 · 2026 马年”在解曰内容读完后再出现。
  // 为了视频里能看到它，放在音频结束前约 0.75 秒显现。
  FOOTER_REVEAL_AT = Math.max(revealAt + 1.2, safeDuration - 0.75);
  return timeline;
}}

function escapeHtmlForCard(s) {{
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}}

function clamp01(v) {{
  return Math.max(0, Math.min(1, Number(v || 0)));
}}

function easeOutCubic(v) {{
  v = clamp01(v);
  return 1 - Math.pow(1 - v, 3);
}}

function easeOutBack(v) {{
  v = clamp01(v);
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(v - 1, 3) + c1 * Math.pow(v - 1, 2);
}}

function ensurePoemDom() {{
  const poemEl = document.getElementById('poemWrite');
  if (!poemEl || POEM_DOM_READY) return;

  const html = POEM_SEGMENTS.map((line, index) => {{
    const effect = index % 2 === 0 ? 'effect-weld' : 'effect-push';
    const safeLine = escapeHtmlForCard(line || '');
    return `<div class="poem-write-line ${{effect}} waiting" data-index="${{index}}" style="--reveal:0%;--p:0;--pushOpacity:0;--pushScale:1.08"><span class="speed-shadow">${{safeLine}}</span><span class="line-glow">${{safeLine}}</span><span class="line-main">${{safeLine}}</span><span class="brush-sweep"></span></div>`;
  }}).join('');

  poemEl.innerHTML = html;
  POEM_DOM_READY = true;
}}

function renderWritingAt(t) {{
  const poemEl = document.getElementById('poemWrite');
  const explanationContent = document.getElementById('explanationContent');
  const expEl = document.getElementById('explanationWrite');
  const footerEl = document.getElementById('footerSeal');
  const visionImg = document.querySelector('.vision-window img');

  ensurePoemDom();

  // 图片自身做轻微“远近呼吸”循环，不使用 45 度流光。
  // 通过 JS 按视频时间推进，确保 Playwright 逐帧截图时缩放也会生效。
  if (visionImg) {{
    const cycle = 4.8;
    const phase = ((Number(t || 0) % cycle) / cycle);
    const wave = (1 - Math.cos(phase * Math.PI * 2)) / 2;
    const imageScale = (1.018 + wave * 0.035).toFixed(4);
    const imageY = (-1.2 * wave).toFixed(2) + 'px';
    visionImg.style.setProperty('--imageScale', imageScale);
    visionImg.style.setProperty('--imageY', imageY);
  }}

  const lineEls = poemEl ? poemEl.querySelectorAll('.poem-write-line') : [];

  POEM_SEGMENTS.forEach((line, index) => {{
    const item = WRITE_TIMELINE.find(x => x.target === 'poem' && x.index === index);
    let progress = 0;
    if (item) {{
      progress = clamp01((t - item.start) / Math.max(0.001, item.end - item.start));
    }}

    const effect = index % 2 === 0 ? 'effect-weld' : 'effect-push';
    const state = progress <= 0 ? 'waiting' : (progress >= 1 ? 'done' : 'writing');
    const lineEl = lineEls[index];
    if (!lineEl) return;

    lineEl.className = `poem-write-line ${{effect}} ${{state}}`;

    if (effect === 'effect-push') {{
      // 第 2、4 句：中心点固定，只叠加“由大到小缩放 + 由虚到实透明度”。
      // 重点：不重建 DOM、不做 X/Y 位移、不改字距、不加影子。
      // 这样可以避免字体每帧重新排版导致的上下抖动。
      const fastProgress = clamp01(progress / 0.52);
      const eased = easeOutCubic(fastProgress);
      const inv = 1 - eased;

      const pushOpacity = progress <= 0 ? '0' : Math.min(1, fastProgress * 5.5).toFixed(3);
      const pushScale = (1 + inv * 0.12).toFixed(4);

      lineEl.style.setProperty('--pushOpacity', pushOpacity);
      lineEl.style.setProperty('--pushScale', pushScale);
      lineEl.style.setProperty('--reveal', '100%');
      lineEl.style.setProperty('--p', eased.toFixed(4));
      return;
    }}

    const eased = easeOutCubic(progress);
    const reveal = (eased * 100).toFixed(2) + '%';
    const p = clamp01(eased).toFixed(4);

    lineEl.style.setProperty('--reveal', reveal);
    lineEl.style.setProperty('--p', p);
    lineEl.style.setProperty('--pushOpacity', progress <= 0 ? '0' : '1');
    lineEl.style.setProperty('--pushScale', '1');
  }});

  if (t >= EXPLANATION_REVEAL_AT) {{
    expEl.textContent = EXPLANATION_FULL_TEXT;
    explanationContent.classList.add('visible');
  }} else {{
    expEl.textContent = '';
    explanationContent.classList.remove('visible');
  }}

  if (footerEl) {{
    if (t >= FOOTER_REVEAL_AT) {{
      footerEl.classList.add('visible');
    }} else {{
      footerEl.classList.remove('visible');
    }}
  }}
}}

window.__setWritingDuration = function(duration) {{
  WRITE_DURATION = Math.max(6, Number(duration || 12));
  WRITE_TIMELINE = buildWritingTimeline(WRITE_DURATION);
  POEM_DOM_READY = false;
  renderWritingAt(0);
}};

window.__setWriteProgress = function(seconds) {{
  if (!WRITE_TIMELINE.length) {{
    WRITE_TIMELINE = buildWritingTimeline(WRITE_DURATION);
  }}
  renderWritingAt(Number(seconds || 0));
}};

window.__setWritingDuration(12);
</script>
</body>
</html>
"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)
    except OSError:
        # 如果当前目录不可写，则自动回退到桌面输出
        filename = os.path.join(OUTPUT_DIR, os.path.basename(filename) or "new_year_blessing.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)
    return filename

# -----------------------
# ✅ 背景音乐：随机 6 首之一
# -----------------------
def pick_random_music(music_pool):
    valid = [p for p in (music_pool or []) if p and os.path.exists(p)]
    if not valid:
        return None
    return random.choice(valid)

def mix_tts_with_bgm(tts_mp3_path, bgm_path, mixed_out_path):
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

    if not bgm_path or not os.path.exists(bgm_path):
        return None

    cmd = [
        ffmpeg_exe, "-y",
        "-i", tts_mp3_path,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        f"[1:a]volume={BGM_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        mixed_out_path
    ]
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return mixed_out_path
    except Exception:
        return None

def capture_html_to_image(html_path, output_img):
    """
    ✅ 替换点（只改这里）：
    - 优先用 Playwright 对 #captureFrame 做元素截图
    - 动态读取 bounding_box 高度并调整 viewport，确保从上到下完整截取，不截断
    - Playwright 不可用再回退到原 imgkit / selenium 方案（其余逻辑不动）
    """
    # ① Playwright 元素截图（优先）
    try:
        from playwright.sync_api import sync_playwright
        import math as _math

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                ]
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=2
            )
            page = context.new_page()

            page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(180)

            locator = page.locator(f"#{CAPTURE_TARGET_ID}")
            locator.wait_for(state="visible", timeout=10000)

            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(80)

            locator.screenshot(path=output_img)

            context.close()
            browser.close()

        if os.path.exists(output_img) and os.path.getsize(output_img) > 1200:
            return True
    except Exception as e:
        print(f"【Playwright截图失败】{e}")
        pass

    # ② 原 imgkit 方案（保持不动）
    try:
        import imgkit
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        options = {
            'width': 1280,
            'height': 720,
            'format': 'png',
            'encoding': 'UTF-8',
            'quiet': '',
            'disable-smart-width': '',
            'enable-local-file-access': ''
        }
        imgkit.from_string(html_content, output_img, options=options)
        if os.path.exists(output_img) and os.path.getsize(output_img) > 0:
            return True
    except Exception:
        pass

    # ③ 原 selenium 方案（保持不动）
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--force-device-scale-factor=2")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--no-first-run")

        driver = None
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            driver.get(f"file://{os.path.abspath(html_path)}")
            time.sleep(1)
            driver.save_screenshot(output_img)
            if os.path.exists(output_img) and os.path.getsize(output_img) > 0:
                return True
        finally:
            if driver:
                driver.quit()
    except Exception:
        pass

    return False


# -----------------------
# ✅ 实时书法字幕：完整句子 / 音频近似对齐 / 金色发光 / 左侧安全区
# -----------------------
def _parse_ffmpeg_duration(stderr_text):
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr_text or "")
    if not m:
        return None
    h, mi, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + sec

def get_media_duration_seconds(ffmpeg_exe, media_path):
    try:
        p = subprocess.run(
            [ffmpeg_exe, "-i", media_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return _parse_ffmpeg_duration(p.stderr)
    except Exception:
        return None

def ass_time(seconds):
    seconds = max(0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

# 字幕只用标点做断句，不把标点显示出来
SUBTITLE_PUNCT_PATTERN = r"[，、。！？；：,.!?;:\n\r]+"

def strip_subtitle_punctuation(s):
    """去掉字幕中不需要展示的标点符号。"""
    return re.sub(r"[，、。！？；：,.!?;:]", "", s or "").strip()

def escape_ass_text(s):
    """
    ASS 字幕安全转义。
    注意：这里不做“硬切字”，只清理 HTML 与 ASS 控制字符。
    """
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("\\", "\\\\").replace("{", "｛").replace("}", "｝")
    return s.strip()

def clean_subtitle_text(s, remove_punctuation=True):
    s = escape_ass_text(s)
    s = re.sub(r"\s+", "", s)
    if remove_punctuation:
        s = strip_subtitle_punctuation(s)
    return s.strip()

def split_text_by_natural_pause(text):
    """
    按自然标点生成字幕段：
    - 逗号、顿号、句号、问号、感叹号、分号、冒号都作为断句信号；
    - 标点只用于切分节奏，不进入最终字幕显示；
    - 不按固定字数硬切成多条字幕，避免出现碎词。
    """
    text = escape_ass_text(text)
    if not text:
        return []

    text = (text
            .replace(",", "，")
            .replace(".", "。")
            .replace("!", "！")
            .replace("?", "？")
            .replace(";", "；")
            .replace(":", "："))

    raw_parts = re.split(SUBTITLE_PUNCT_PATTERN, text)
    result = []
    for part in raw_parts:
        part = clean_subtitle_text(part, remove_punctuation=True)
        if not part:
            continue

        # 过短的残片并回上一句，避免单字/双字孤立闪现
        if result and len(part) <= 2:
            result[-1] += part
        else:
            result.append(part)

    return [x for x in result if x]

def remove_explanation_label(text):
    """
    字幕展示时去掉“解曰”这两个提示字，但保留后面的解曰内容。
    例如：
    - 【解曰】2026丙午马年... -> 2026丙午马年...
    - 解曰：事业有进... -> 事业有进...
    """
    text = text or ""
    text = re.sub(r"^\s*[【\[]?\s*解曰\s*[】\]]?\s*[：:。,.，、；;!！?？-]*\s*", "", text)
    text = re.sub(r"[【\[]?\s*解曰\s*[】\]]?\s*[：:。,.，、；;!！?？-]*", "", text)
    return text.strip()

def build_live_subtitle_segments(fortune_data):
    """
    生成与 TTS 对齐的字幕段。
    说明：
    - 签诗内容展示字幕；
    - 解曰内容也展示字幕；
    - 只是不展示“解曰”这两个字；
    - 逗号、顿号、句号、问号、感叹号、分号、冒号只作为断句信号，不进入最终字幕显示。
    """
    segments = []

    raw_poem = fortune_data.get("poem", "") or ""
    poem_text = re.sub(r"<br\s*/?>", "\n", raw_poem)
    poem_text = re.sub(r"<[^>]+>", "", poem_text)

    # 优先按 <br>/换行切签诗；如果没有换行，再按标点切。
    poem_lines = [clean_subtitle_text(x, remove_punctuation=True) for x in poem_text.split("\n")]
    poem_lines = [x for x in poem_lines if x]
    if len(poem_lines) <= 1:
        poem_lines = split_text_by_natural_pause(poem_text)

    for line in poem_lines:
        segments.append({
            "text": line,
            "kind": "poem",
        })

    # 解曰内容也要展示，但去掉“解曰”两个字本身。
    explanation_text = remove_explanation_label(fortune_data.get("explanation", "") or "")
    explanation_lines = split_text_by_natural_pause(explanation_text)
    for line in explanation_lines:
        segments.append({
            "text": line,
            "kind": "explanation",
        })

    return segments[:80]

def subtitle_read_weight(text, kind="poem"):
    """
    用文本长度估算每段字幕占用时长。
    诗句通常读得更慢一点，解曰内容通常更接近口播说明。
    """
    text = strip_subtitle_punctuation(text or "")
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_count = len(re.findall(r"[A-Za-z0-9]", text))
    weight = cjk_count * 1.0 + ascii_count * 0.55
    if kind == "poem":
        weight += 1.8
    else:
        weight += 0.8
    return max(1.8, weight)

def allocate_subtitle_timeline(segments, audio_duration):
    """
    根据音频总时长 + 每段字幕阅读权重分配时间轴。
    TTS 文本结构是：签诗 + “解曰。” + explanation。
    画面里不显示“解曰”两个字，所以在签诗和解曰内容之间预留一个短 gap，
    让语音读到“解曰”时画面不显示这两个字，也不提前露出解释内容。
    """
    duration = max(float(audio_duration or 8), 8.0)
    start_offset = max(0.0, float(SUBTITLE_START_OFFSET))
    end_padding = 0.45

    has_poem = any(seg.get("kind") == "poem" for seg in segments)
    has_explanation = any(seg.get("kind") == "explanation" for seg in segments)
    label_gap = 0.78 if has_poem and has_explanation else 0.0

    available = max(1.0, duration - start_offset - end_padding - label_gap)
    weights = [subtitle_read_weight(seg["text"], seg.get("kind", "poem")) for seg in segments]
    total_weight = sum(weights) or 1.0

    timeline = []
    cursor = start_offset
    prev_kind = None

    for seg, weight in zip(segments, weights):
        kind = seg.get("kind", "poem")

        # 这里专门避开 TTS 里的“解曰。”，不展示这两个字。
        if prev_kind == "poem" and kind == "explanation" and label_gap > 0:
            cursor += label_gap

        part_duration = available * weight / total_weight
        part_duration = max(1.1, part_duration)

        st = cursor
        ed = min(cursor + part_duration, duration - end_padding)
        cursor = ed

        clean_text = strip_subtitle_punctuation(remove_explanation_label(seg["text"]))
        if clean_text and ed > st + 0.35:
            timeline.append({
                "start": st,
                "end": ed,
                "text": clean_text,
                "kind": kind,
            })

        prev_kind = kind

    return timeline

def _split_long_line_without_tiny_tail(line, wrap_chars):
    """
    仅用于同一条字幕内部的视觉换行。
    尽量避免最后一行只剩 1～2 个字，降低“碎词感”。
    """
    line = strip_subtitle_punctuation(line)
    if len(line) <= wrap_chars + 2:
        return [line]

    chunks = []
    rest = line
    while len(rest) > wrap_chars + 2:
        chunks.append(rest[:wrap_chars])
        rest = rest[wrap_chars:]

    if rest:
        if chunks and len(rest) <= 2:
            need = 4 - len(rest)
            move = min(max(need, 1), max(1, len(chunks[-1]) - 6))
            rest = chunks[-1][-move:] + rest
            chunks[-1] = chunks[-1][:-move]
        chunks.append(rest)

    return [x for x in chunks if x]


def wrap_ass_subtitle_text(text, wrap_chars=None):
    """
    单条字幕内部换行。
    说明：
    - 标点不显示；
    - 不使用 ASS clip 裁剪；
    - 只在同一条字幕内部换行，不拆成多个时间段。
    """
    wrap_chars = int(wrap_chars or SUBTITLE_WRAP_CHARS)
    text = clean_subtitle_text(text, remove_punctuation=True)
    if not text:
        return ""

    if len(text) <= wrap_chars + 2:
        return text

    lines = _split_long_line_without_tiny_tail(text, wrap_chars)
    if len(lines) > 2:
        lines = [lines[0], "".join(lines[1:])]
    return r"\N".join(lines)

def make_ass_live_subtitles(fortune_data, audio_duration, output_ass_path):
    segments = build_live_subtitle_segments(fortune_data)
    if not segments:
        return None

    timeline = allocate_subtitle_timeline(segments, audio_duration)
    if not timeline:
        return None

    fade_ms = 260

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{SUBTITLE_FONT_NAME},{SUBTITLE_FONT_SIZE},&H0036D7FF,&H000000FF,&H00321800,&H00000000,1,0,0,0,100,100,0.8,0,1,1.15,0,5,40,40,0,1
Style: Glow,{SUBTITLE_FONT_NAME},{SUBTITLE_FONT_SIZE},&H0000F2FF,&H000000FF,&H0000C8FF,&H00000000,1,0,0,0,100,100,0.8,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    for item in timeline:
        st = item["start"]
        ed = item["end"]
        if ed <= st + 0.35:
            continue

        display_text = wrap_ass_subtitle_text(item["text"])
        if not display_text:
            continue

        seg_duration_ms = max(600, int((ed - st) * 1000))
        grow_1 = int(seg_duration_ms * 0.38)
        grow_2 = int(seg_duration_ms * 0.76)

        # Glow 层：金色外发光。不再使用 \clip 裁剪，避免画面出现硬切边。
        glow_tag = (
            "{"
            f"\\an5\\pos({SUBTITLE_SAFE_X},{SUBTITLE_SAFE_Y})\\fad({fade_ms},{fade_ms})"
            "\\blur10\\bord0"
            f"\\fs{SUBTITLE_FONT_SIZE}\\fsp0.8"
            f"\\t(0,{grow_1},\\fs{SUBTITLE_FONT_SIZE+2}\\fsp1.6\\blur13)"
            f"\\t({grow_1},{grow_2},\\fs{SUBTITLE_FONT_SIZE+3}\\fsp2.2\\blur15)"
            "}"
        )

        # Main 层：金色书法正文，深色描边，保持可读。不再裁剪。
        main_tag = (
            "{"
            f"\\an5\\pos({SUBTITLE_SAFE_X},{SUBTITLE_SAFE_Y})\\fad({fade_ms},{fade_ms})"
            "\\blur0.2\\bord1.35"
            f"\\fs{SUBTITLE_FONT_SIZE}\\fsp0.8"
            f"\\t(0,{grow_1},\\fs{SUBTITLE_FONT_SIZE+2}\\fsp1.3)"
            f"\\t({grow_1},{grow_2},\\fs{SUBTITLE_FONT_SIZE+3}\\fsp1.8)"
            "}"
        )

        events.append(f"Dialogue: 0,{ass_time(st)},{ass_time(ed)},Glow,,0,0,0,,{glow_tag}{display_text}")
        events.append(f"Dialogue: 1,{ass_time(st)},{ass_time(ed)},Main,,0,0,0,,{main_tag}{display_text}")

    if not events:
        return None

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    return output_ass_path

def escape_ffmpeg_filter_path(path):
    # ffmpeg subtitles filter path escaping
    p = os.path.abspath(path)
    p = p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return p

def capture_html_write_animation_to_frames(html_path, frames_dir, duration_seconds, fps=WRITE_ANIMATION_FPS):
    """用 Playwright 按时间轴截取页签内动态写字效果。

    这版修复点：
    - 补齐 WRITE_FRAME_EXT / WRITE_FRAME_QUALITY，避免运行时报 NameError。
    - 不再把扩展名写成字面量 {WRITE_FRAME_EXT}。
    - 截图前等待 JS 写字函数就绪，避免页面未初始化导致捕获失败。
    - 清空旧帧目录，避免 ffmpeg 读取到历史残留帧。
    - JPEG 截图失败时自动降级 PNG 截图，并返回实际使用的帧格式。
    """
    try:
        from playwright.sync_api import sync_playwright
        import shutil

        duration_seconds = max(1.0, float(duration_seconds or 8))
        fps = max(4, int(fps or WRITE_ANIMATION_FPS))
        total_frames = max(2, int(duration_seconds * fps) + 1)

        if os.path.isdir(frames_dir):
            shutil.rmtree(frames_dir, ignore_errors=True)
        os.makedirs(frames_dir, exist_ok=True)

        preferred_ext = WRITE_FRAME_EXT
        actual_ext = preferred_ext

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--allow-file-access-from-files",
                    "--font-render-hinting=none",
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=2,
                java_script_enabled=True,
            )
            page = context.new_page()
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("console", lambda msg: page_errors.append(f"{msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)
            page.goto(f"file://{os.path.abspath(html_path)}", wait_until="domcontentloaded", timeout=30000)

            # 网络资源如果有加载慢，不强依赖；页面主体和 JS 函数就绪才是关键。
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            locator = page.locator(f"#{CAPTURE_TARGET_ID}")
            locator.wait_for(state="visible", timeout=15000)

            try:
                page.wait_for_function("typeof window.__setWritingDuration === 'function' && typeof window.__setWriteProgress === 'function'", timeout=15000)
            except Exception as e:
                html_debug = ""
                try:
                    html_debug = page.content()[:1600]
                except Exception:
                    pass
                msg = "\n".join(page_errors[-8:])
                raise RuntimeError(f"页面写字函数没有成功初始化，可能是 HTML/JS 语法错误。原始错误: {e}. 页面错误: {msg}. HTML片段: {html_debug}")

            page.evaluate("duration => window.__setWritingDuration(duration)", duration_seconds)
            page.evaluate("() => document.fonts && document.fonts.ready ? document.fonts.ready : true")
            page.wait_for_timeout(120)

            # 先截第 0 帧验证截图格式是否可用；如果 JPEG 出错，则自动降级 PNG。
            def screenshot_one(path, ext):
                if ext == "jpg":
                    locator.screenshot(
                        path=path,
                        type="jpeg",
                        quality=max(55, min(100, int(WRITE_FRAME_QUALITY)))
                    )
                else:
                    locator.screenshot(path=path, type="png")

            for frame in range(total_frames):
                t = min(duration_seconds, frame / fps)
                page.evaluate("seconds => window.__setWriteProgress(seconds)", t)
                page.wait_for_timeout(4)

                frame_path = os.path.join(frames_dir, f"frame_{frame:04d}.{actual_ext}")
                try:
                    screenshot_one(frame_path, actual_ext)
                except Exception:
                    if actual_ext != "png":
                        # 首帧失败时整体切换到 PNG；清理已生成帧，重新从 0 开始更安全。
                        actual_ext = "png"
                        for name in os.listdir(frames_dir):
                            if name.startswith("frame_"):
                                try:
                                    os.remove(os.path.join(frames_dir, name))
                                except Exception:
                                    pass
                        frame_path = os.path.join(frames_dir, f"frame_{frame:04d}.{actual_ext}")
                        screenshot_one(frame_path, actual_ext)
                    else:
                        raise

            context.close()
            browser.close()

        first_frame = os.path.join(frames_dir, f"frame_0000.{actual_ext}")
        if not os.path.exists(first_frame) or os.path.getsize(first_frame) < 1000:
            return 0, actual_ext

        return total_frames, actual_ext
    except Exception as e:
        print(f"【动态写字帧捕获失败】{e}")
        return 0, WRITE_FRAME_EXT

def generate_video(html_path, audio_bytes, music_pool, fortune_data=None):
    print("正在为您描绘这幅锦绣签程（预计1分钟）...")

    try:
        import imageio_ffmpeg
    except ImportError:
        print("❌ 缺少 imageio-ffmpeg 依赖，无法合成视频")
        return None

    frames_dir = os.path.join(OUTPUT_DIR, "temp_write_frames")
    temp_tts = os.path.join(OUTPUT_DIR, "temp_tts.mp3")
    temp_mix = os.path.join(OUTPUT_DIR, "temp_mix.mp3")

    with open(temp_tts, "wb") as f:
        f.write(audio_bytes)

    bgm = pick_random_music(music_pool)
    mixed_audio = mix_tts_with_bgm(temp_tts, bgm, temp_mix) if bgm else None
    final_audio_path = mixed_audio if mixed_audio and os.path.exists(mixed_audio) else temp_tts

    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        audio_duration = get_media_duration_seconds(ffmpeg_exe, final_audio_path) or 8

        frame_count, actual_frame_ext = capture_html_write_animation_to_frames(
            html_path,
            frames_dir,
            duration_seconds=audio_duration,
            fps=WRITE_ANIMATION_FPS
        )
        if frame_count <= 0:
            print("❌ 动态写字画面捕获失败，无法生成视频")
            return None

        cmd = [
            ffmpeg_exe, "-y",
            "-framerate", str(WRITE_ANIMATION_FPS),
            "-i", os.path.join(frames_dir, f"frame_%04d.{actual_frame_ext}"),
            "-i", final_audio_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1280:720:flags=lanczos,format=yuv420p",
            "-shortest",
            VIDEO_OUTPUT_FILENAME
        ]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(VIDEO_OUTPUT_FILENAME):
            print("❌ 视频文件未生成")
            return None

        if os.path.getsize(VIDEO_OUTPUT_FILENAME) < 1000:
            print("❌ 视频文件损坏")
            try:
                os.remove(VIDEO_OUTPUT_FILENAME)
            except Exception:
                pass
            return None

        return VIDEO_OUTPUT_FILENAME

    except Exception as e:
        print(f"❌ 视频合成失败: {e}")
        if os.path.exists(VIDEO_OUTPUT_FILENAME):
            try:
                os.remove(VIDEO_OUTPUT_FILENAME)
            except Exception:
                pass
        return None
    finally:
        for p in [temp_tts, temp_mix]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        if os.path.isdir(frames_dir):
            try:
                import shutil
                shutil.rmtree(frames_dir, ignore_errors=True)
            except Exception:
                pass


def get_api_key(api_key_arg=None):
    api_key = api_key_arg or os.getenv("ARK_API_KEY", "7d19f69b-b938-4e75-8046-3ae5ec1d8a27") or os.getenv("VOLC_ARK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少火山方舟 API 密钥。请设置 ARK_API_KEY，或使用 --api-key 传入。")
    return api_key

def get_tts_api_key(tts_api_key_arg=None):
    load_local_env()
    return (
        tts_api_key_arg
        or os.getenv("OPEN_SPEECH_X_API_KEY")
        or os.getenv("VOLC_TTS_API_KEY")
        or DEFAULT_OPEN_SPEECH_X_API_KEY
    )

def parse_music_files_arg(s):
    if not s:
        return None
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return parts or None

def main():
    parser = argparse.ArgumentParser(description="2026新年祈福")
    parser.add_argument("--user-info", type=str, help="用户信息")
    parser.add_argument("--api-key", type=str, help="API Key")
    parser.add_argument("--tts-api-key", type=str, help="火山 Open Speech TTS x-api-key")
    parser.add_argument("--music-files", type=str, help="背景音乐路径（逗号分隔），不传则自动加载 assets 音乐池")
    parser.add_argument("--output-format", type=str, default="video", choices=["video"], help="输出格式: video")
    parser.add_argument("--seed", type=str, default="", help="可选：抽签随机种子（为空则自动）")
    args = parser.parse_args()

    user_input = args.user_info
    if not user_input:
        if sys.stdin.isatty():
            print("请输入祈愿信息 (例: 我叫李云龙，男，ESTP，求事业顺利):")
            user_input = input("👉 ").strip()
        else:
            user_input = "我叫李云龙，男，1995年10月1日出生，ESTP，2026年想要平安幸福"

    music_pool = parse_music_files_arg(args.music_files) or DEFAULT_MUSIC_POOL

    seed_text = (args.seed or "").strip()
    if not seed_text:
        seed_text = f"{int(time.time())}-{user_input[:24]}-{random.randint(0, 10_000_000)}"
    rng = random.Random(seed_text)
    forced_type = pick_fortune_type(rng)

    print("正在锚定时空坐标，解析命运波段...")
    try:
        api_key = get_api_key(args.api_key)
    except RuntimeError as e:
        print(f"\n【失败】{e}")
        return 1

    tts_api_key = get_tts_api_key(args.tts_api_key)
    if not tts_api_key:
        print("\n【失败】缺少 OPEN_SPEECH_X_API_KEY，无法生成最终 MP4 视频。")
        return 1

    fortune = get_fortune_content(user_input, api_key, forced_type=forced_type)

    if not fortune:
        print("\n【失败】天人感应未获响应。")
        return 1

    fortune["type"] = normalize_type(forced_type) or fortune.get("type") or "上吉"

    print("因果模型收敛完成，正在生成全息神谕...")
    img_uri = generate_image_background(fortune, api_key, forced_type=fortune["type"], user_sentence=user_input)
    audio_bytes = generate_tts_audio(fortune, tts_api_key)

    if not audio_bytes:
        print("\n【失败】语音合成失败，无法生成最终 MP4 视频。")
        return 1

    html_path = save_final_html(fortune, img_uri, False, "")
    video_path = generate_video(html_path, audio_bytes, music_pool, fortune)

    if not video_path:
        print("\n【失败】视频合成失败，未生成最终 MP4。")
        return 1

    print(f"\n【完成】HTML已生成：{os.path.abspath(html_path)}")
    print(f"【完成】视频已生成：{os.path.abspath(video_path)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
