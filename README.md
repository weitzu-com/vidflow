# vidflow — AI 短视频自动生产 SDK

从剧本到成片，五阶段全自动流水线。

```
剧本创作 → AI视频(Seedance) → TTS语音(SAMI/edge-tts) → FFmpeg合成 → 成片
```

## 快速开始

```bash
# 安装
pip install vidflow

# 设置 API Key
export ARK_API_KEY="your-volcengine-ark-api-key"

# 一键生成
python -m vidflow.pipeline --topic "安史之乱" --style dark_cinematic --duration 60
```

## Python API

```python
from vidflow import Pipeline
from vidflow.pipeline import ScriptSegment

pipe = Pipeline(api_key="your-key", style="dark_cinematic", voice="documentary")

segments = [
    ScriptSegment("hook", "大唐的毁灭，真的是因为一个女人吗？错。", 11, "split_screen"),
    ScriptSegment("twist", "边疆四十九万边防军，长安不到十三万。", 14, "map"),
    ScriptSegment("climax", "渔阳鼙鼓动地来！安禄山反了。", 18, "battle"),
    ScriptSegment("aftermath", "八百九十万户，战后不足两百万。", 15, "ruins"),
]

result = pipe.run(segments, output_name="my_video.mp4")
print(f"✅ {result.output_path} ({result.size_mb:.1f}MB)")
```

## 功能特性

| 功能 | 支持 |
|------|------|
| AI 视频生成 | Seedance 2.0 (火山引擎) |
| TTS 语音 | SAMI (剪映) / edge-tts / macOS say |
| 视觉风格 | 暗黑史诗 / 温暖纪录片 / 科技感 / 古风 |
| 音色 | 沉稳解说 / 激昂旁白 / 舌尖解说 / 纪录片 |
| 合成 | FFmpeg 暗黑调色 + BGM混音 + 精确字幕 |
| 并行 | 视频并行生成 (10x speedup) |

## 环境要求

- Python 3.9+
- FFmpeg (含 libass，字幕支持): `brew install ffmpeg-full`
- 火山引擎 ARK API Key (免费注册: ark.cn-beijing.volces.com)

## 项目结构

```
vidflow/
├── vidflow/           ← SDK 包
│   ├── pipeline.py    ← 流水线编排
│   ├── tts.py         ← TTS 抽象层
│   ├── video.py       ← Seedance API
│   ├── assemble.py    ← FFmpeg 合成
│   └── prompts.py     ← 提示词模板库
├── tests/             ← 单元测试
├── examples/anshi/    ← 完整示例: 安史之乱
├── docs/              ← 文档
├── .github/workflows/ ← CI/CD
└── pyproject.toml
```

## 完整文档

详见 [docs/用户手册.md](docs/用户手册.md)

## License

MIT
