---
name: new-year-fortune
description: 生成2026马年新年签运，包括AI推演运势、生成祈福金榜HTML页面、TTS语音合成、背景音乐混音及最终视频输出
dependency:
  python:
    - selenium>=4.0.0
    - webdriver-manager>=4.0.0
    - imageio-ffmpeg>=0.5.0
    - requests>=2.28.0
---

# 新年签运生成技能

## 任务目标
- 本 Skill 用于:生成2026马年新年签运，包含运势推演、祈福金榜页面、语音解说、背景音乐混音及最终视频输出
- 能力包含:AI运势推演、图片生成、语音合成、视频合成、HTML页面生成
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
     - 可选参数: `--output-format "html|video|both"` (输出格式，默认为both)
  3. 智能体等待脚本执行完成
  4. 根据输出格式返回结果:
     - HTML文件: `new_year_blessing.html` (祈福金榜页面，包含保存视频按钮)
     - 视频文件: `new_year_blessing_video.mp4` (签运视频，包含TTS人声+背景音乐混音)
     - 或两者同时输出
- 可选分支:
  - 当 仅需HTML:使用 `--output-format html` 参数，快速生成祈福页面
  - 当 截图工具不可用:提示用户安装 wkhtmltopdf 或 Chrome
  - 当 需要自定义音乐:可使用 `--music-files "音乐路径1,音乐路径2,..."` 参数指定音乐文件

## 资源索引
- 必要脚本:见 [scripts/happynewyear.py](scripts/happynewyear.py)(用途:生成新年签运HTML页面和/或视频;参数:--user-info用户信息,--api-key API密钥,--music-files自定义音乐路径,--output-format输出格式(html/video/both);输出:new_year_blessing.html、new_year_blessing_video.mp4)
- 领域参考:无
- 输出资产:见 [assets/](assets/)(包含背景音乐文件)

## 注意事项
- 脚本会自动安装缺失的 Python 依赖
- 默认输出格式为 `both`，同时生成 HTML 页面和视频文件
- 若只需 HTML 页面，可使用 `--output-format html` 参数，快速生成祈福页面（无需截图工具）
- 视频生成需要截图工具，脚本会优先使用 imgkit（需要 wkhtmltopdf），失败则尝试 selenium（需要 Chrome）
- HTML 页面包含"保存视频"按钮，点击后可下载对应的视频文件
- 如果没有安装截图工具，视频生成会跳过，但仍可输出 HTML 页面
- 背景音乐默认使用assets目录下的chinese-new-year.mp3和new-year.mp3
- API密钥优先级:命令行参数 > 环境变量ARK_API_KEY > 默认密钥

## 使用示例
```bash
# 基础使用（同时生成HTML和视频）
python scripts/happynewyear.py --user-info "我叫李云龙，男，1995年10月1日出生，ESTP，2026年想要平安幸福"

# 仅生成HTML页面（快速）
python scripts/happynewyear.py --user-info "我叫张三，女，2000年5月20日出生，求事业顺利" --output-format html

# 仅生成视频
python scripts/happynewyear.py --user-info "我叫王五，求健康平安" --output-format video

# 使用自定义API密钥
python scripts/happynewyear.py --user-info "我叫赵六，求财运亨通" --api-key "your-api-key"

# 使用自定义背景音乐
python scripts/happynewyear.py --user-info "我叫孙七，求家庭幸福" --music-files "music1.mp3,music2.mp3"
```
