---
name: new-year-fortune
description: 生成2026马年新年签运，包括AI推演运势、TTS语音合成、背景音乐混音及最终MP4视频输出
dependency:
  python:
    - selenium>=4.0.0
    - webdriver-manager>=4.0.0
    - imageio-ffmpeg>=0.5.0
    - requests>=2.28.0
---

# 新年签运生成技能

## 任务目标
- 本 Skill 用于:生成2026马年新年签运，包含运势推演、语音解说、背景音乐混音及最终MP4视频输出
- 能力包含:AI运势推演、图片生成、语音合成、视频合成。HTML只作为内部截图/渲染中间产物，不作为用户交付物
- 视频规格:横屏 16:9 MP4，使用生成图作为全画幅高斯模糊背景，中间居中展示清晰竖版签卡
- 签诗要求:每句必须包含中文逗号，便于语音模型自然断句
- 字幕要求:视频左侧展示书法诗词风格光效字幕，透明度渐显、光效增强、字距和字号变大后渐隐
- 触发条件:用户询问新年运势、抽签、祈福等需求

## 前置准备
- 依赖说明:脚本需要selenium、webdriver-manager、imageio-ffmpeg等库
  ```
  imageio-ffmpeg>=0.5.0
  # 视频生成需要以下任选其一（推荐 imgkit）
  imgkit>=1.2.0  # 轻量级，需要系统安装 wkhtmltopdf
  # 或
  selenium>=4.0.0
  webdriver-manager>=4.0.0  # 需要完整 Chrome 浏览器
  ```
- 系统依赖（视频生成必需）:
  - **方案1（推荐）**: 安装 `wkhtmltopdf`
    ```bash
    # Ubuntu/Debian
    apt-get install wkhtmltopdf
    
    # CentOS/RHEL
    yum install wkhtmltopdf
    
    # macOS
    brew install wkhtmltopdf
    ```
  - **方案2（备用）**: 安装 Chrome 浏览器（selenium 依赖）
- 非标准文件/文件夹准备:无

## 操作步骤
- 标准流程:
  1. 用户输入祈愿信息（姓名、性别、出生日期、性格、祈愿等）
  2. 调用 `scripts/happynewyear.py` 生成新年签运
     - 脚本参数: `--user-info "祈愿信息"`
     - 可选参数: `--api-key "API密钥"` (使用环境变量ARK_API_KEY作为默认值)
     - 固定使用参数: `--output-format video` (用户交付物必须是MP4)
  3. 智能体等待脚本执行完成
  4. 返回视频文件: `new_year_blessing_video.mp4` (签运视频，包含TTS人声+背景音乐混音)
  5. 不向用户返回 `new_year_blessing.html`，除非用户明确要求调试中间产物
- 可选分支:
  - 当 截图工具不可用:提示用户安装 wkhtmltopdf 或 Chrome
  - 当 需要自定义音乐:可使用 `--music-files "音乐路径1,音乐路径2,..."` 参数指定音乐文件

## 资源索引
- 必要脚本:见 [scripts/happynewyear.py](scripts/happynewyear.py)(用途:生成新年签运MP4视频;参数:--user-info用户信息,--api-key API密钥,--music-files自定义音乐路径,--output-format video;输出:new_year_blessing_video.mp4)
- 领域参考:无
- 输出资产:见 [assets/](assets/)(包含背景音乐文件)

## 注意事项
- 脚本会自动安装缺失的 Python 依赖
- 默认对用户交付 `new_year_blessing_video.mp4`
- 不要把 `new_year_blessing.html` 当作输出结果；它只是视频截图/渲染中间产物
- 视频生成需要截图工具，脚本会优先使用 imgkit（需要 wkhtmltopdf），失败则尝试 selenium（需要 Chrome）
- 如果没有安装截图工具，应说明MP4生成失败，不要用HTML替代交付
- 背景音乐默认加载 `assets/` 目录下所有支持的音频文件（`.mp3`, `.wav`, `.m4a`, `.aac`, `.flac`, `.ogg`）
- API密钥优先级:命令行参数 > 环境变量ARK_API_KEY > 默认密钥

## 使用示例
```bash
# 基础使用（生成MP4视频）
python scripts/happynewyear.py --user-info "我叫李云龙，男，1995年10月1日出生，ESTP，2026年想要平安幸福" --output-format video

# 使用自定义API密钥
python scripts/happynewyear.py --user-info "我叫赵六，求财运亨通" --api-key "your-api-key" --output-format video

# 使用自定义背景音乐
python scripts/happynewyear.py --user-info "我叫孙七，求家庭幸福" --music-files "music1.mp3,music2.mp3" --output-format video
```
