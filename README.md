# New Year Fortune Skill

生成 2026 马年新年签运视频，包括运势推演、祈福金榜 HTML、TTS 语音、背景音乐混音与 MP4 视频输出。

## 使用方式

```bash
export ARK_API_KEY="your-api-key"

python scripts/happynewyear.py \
  --user-info "我叫张三，2026年想事业顺利" \
  --output-format video \
  --output-dir output
