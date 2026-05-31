"""
五阶段流水线编排器 v2
剧本 → 视频 → TTS → 合成 → 审查
适配 TTS v2 统一接口
"""
import os, json, time as _time
from dataclasses import dataclass, field
from typing import List, Optional
from .tts import auto_detect_tts, TTSProvider, TTSSynthesis
from .video import SeedanceProvider, VideoScene
from .assemble import FFmpegAssembler
from .prompts import get_scene_prompt, apply_style


@dataclass
class ScriptSegment:
    name: str
    text: str
    duration_sec: int
    scene_type: str = "palace"


@dataclass
class PipelineResult:
    output_path: str
    duration_sec: float
    size_mb: float
    tts_synthesis: Optional[TTSSynthesis] = None
    video_paths: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class Pipeline:
    def __init__(self, api_key: str = None, output_dir: str = "./output",
                 style: str = "dark_cinematic", voice: str = "documentary",
                 tts_provider: TTSProvider = None):
        self.api_key = api_key or os.environ.get("ARK_API_KEY", "")
        self.output_dir = output_dir
        self.style = style
        self.voice = voice
        self.tts = tts_provider or auto_detect_tts()
        self.assembler = FFmpegAssembler()
        os.makedirs(output_dir, exist_ok=True)

        self.seedance = SeedanceProvider(
            self.api_key, output_dir=os.path.join(output_dir, "videos")
        ) if self.api_key else None

    def run(self, segments: List[ScriptSegment], bgm_path: str = None,
            output_name: str = "final.mp4") -> PipelineResult:
        errors = []

        # 阶段1: 视频
        video_paths = []
        if self.seedance:
            scenes = []
            for seg in segments:
                prompt = get_scene_prompt(seg.scene_type, self.style) or apply_style(
                    f"{seg.name} scene, cinematic quality, {self.style}", self.style
                )
                scenes.append(VideoScene(name=seg.name, prompt=prompt, duration=seg.duration_sec))
            try:
                results = self.seedance.generate_all(scenes)
                video_paths = [p for p in results.values() if p]
            except Exception as e:
                errors.append(f"Video generation: {e}")

        # 阶段2: TTS
        synthesis = None
        try:
            texts = [s.text for s in segments]
            synthesis = self.tts.synthesize(texts, voice=self.voice)
        except Exception as e:
            errors.append(f"TTS: {e}")

        # 阶段3: 字幕
        subtitles = []
        if synthesis and synthesis.segments:
            for seg in synthesis.segments:
                subtitles.append((seg.start_sec, seg.start_sec + seg.duration_sec, seg.text))

        # 阶段4: 合成
        output_path = os.path.join(self.output_dir, output_name)
        total_dur = synthesis.total_duration_sec if synthesis else sum(s.duration_sec for s in segments)
        try:
            self.assembler.assemble(
                video_paths=video_paths,
                audio_paths=synthesis.audio_paths if synthesis else [],
                subtitles=subtitles,
                output_path=output_path,
                bgm_path=bgm_path,
                color_style=self.style,
                total_audio_dur=total_dur,
            )
        except Exception as e:
            errors.append(f"Assembly: {e}")

        size_mb = os.path.getsize(output_path) / 1e6 if os.path.exists(output_path) else 0
        return PipelineResult(
            output_path=output_path, duration_sec=total_dur, size_mb=size_mb,
            tts_synthesis=synthesis, video_paths=video_paths, errors=errors,
        )
