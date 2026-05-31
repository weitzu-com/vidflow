"""
vidflow — AI 短视频自动生产 SDK
================================
从剧本到成片，五阶段全自动流水线。
支持 Seedance AI 视频 + SAMI/edge-tts/macOS TTS + FFmpeg 合成。

使用:
    from vidflow import Pipeline
    pipe = Pipeline(api_key="...")
    pipe.run(topic="安史之乱", style="dark_cinematic", duration=60)
"""

from .pipeline import Pipeline
from .tts import TTSProvider, SAMITTS, EdgeTTS, MacOSTTS
from .video import SeedanceProvider
from .assemble import FFmpegAssembler
from .prompts import PROMPT_TEMPLATES, apply_style

__version__ = "0.1.0"
__all__ = [
    "Pipeline", "TTSProvider", "SAMITTS", "EdgeTTS", "MacOSTTS",
    "SeedanceProvider", "FFmpegAssembler", "PROMPT_TEMPLATES", "apply_style",
]
