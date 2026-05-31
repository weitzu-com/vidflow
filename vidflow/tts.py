"""
TTS 语音合成抽象层 v2
支持 SAMI(剪映) / edge-tts(微软) / macOS say
统一接口: synthesize() -> TTSSynthesis
"""
import glob
import os
import subprocess
import sys
import tempfile
import time as _time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List


@dataclass
class TTSSegment:
    text: str
    audio_path: str
    start_sec: float
    duration_sec: float


@dataclass
class TTSSynthesis:
    segments: List[TTSSegment]
    audio_paths: List[str]
    total_duration_sec: float
    provider_name: str
    generated_at: float = field(default_factory=_time.time)


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, segments: List[str], voice: str = "default") -> TTSSynthesis:
        ...


@contextmanager
def _temp_workdir():
    d = tempfile.mkdtemp(prefix="vidflow_tts_")
    try:
        yield d
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


class SAMITTS(TTSProvider):
    """剪映内置 SAMI TTS"""

    RECOMMENDED_VOICES = {
        "documentary": "BV701_streaming",
        "epic": "ICL_zh_male_jilupianjmh",
        "food": "zh_male_commentate_emo_neutral",
        "nature": "zh_male_rendongteng",
        "movie": "BV411_streaming",
        "child": "zh_female_xiaopengyou",
    }

    def __init__(self, projects_root: str = None):
        if projects_root is None:
            projects_root = os.path.expanduser(
                "~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
            )
        os.environ["JY_PROJECTS_ROOT"] = projects_root
        self._provider_name = "sami"

    def synthesize(self, segments: List[str], voice: str = "documentary") -> TTSSynthesis:
        speaker = self.RECOMMENDED_VOICES.get(voice, voice)
        skill_root = os.path.expanduser("~/.claude/skills/jianying-editor")

        _orig_path = list(sys.path)
        sys.path.insert(0, os.path.join(skill_root, "scripts"))
        try:
            from jy_wrapper import JyProject
        finally:
            sys.path[:] = _orig_path

        project = JyProject("vidflow_tts", overwrite=True)
        cursor = 0
        results = []

        for text in segments:
            end = project.add_narrated_subtitles(
                text=text, speaker=speaker, start_time=cursor, track_name="TTS"
            )
            if end:
                dur = (end - cursor) / 1e6
            else:
                dur = max(1.0, len(text) * 0.25)
                end = cursor + int(dur * 1e6)

            results.append(TTSSegment(
                text=text, audio_path="",
                start_sec=cursor / 1e6, duration_sec=dur
            ))
            cursor = end + 300000

        result = project.save()
        draft_path = result.get("draft_path", "") if result else ""
        ogg_files = sorted(
            glob.glob(os.path.join(draft_path, "temp_assets", "tts_*.ogg")),
            key=os.path.getmtime,
        ) if draft_path else []

        for i, seg in enumerate(results):
            if i < len(ogg_files):
                seg.audio_path = ogg_files[i]

        return TTSSynthesis(
            segments=results,
            audio_paths=ogg_files,
            total_duration_sec=cursor / 1e6,
            provider_name="sami",
        )


class EdgeTTS(TTSProvider):
    """微软 Edge TTS — 免费，中国大陆可能受限"""

    def synthesize(self, segments: List[str], voice: str = "zh-CN-YunxiNeural") -> TTSSynthesis:
        try:
            import edge_tts
        except ImportError:
            raise ImportError("pip install edge-tts")
        import asyncio

        async def _synth():
            results = []
            audio_paths = []
            cursor = 0.0
            with _temp_workdir() as workdir:
                for i, text in enumerate(segments):
                    out = os.path.join(workdir, f"seg_{i:03d}.mp3")
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(out)
                    dur = float(subprocess.run(
                        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{out}"',
                        shell=True, capture_output=True, text=True
                    ).stdout.strip() or "2.0")
                    results.append(TTSSegment(text=text, audio_path=out, start_sec=cursor, duration_sec=dur))
                    audio_paths.append(out)
                    cursor += dur + 0.15
                return TTSSynthesis(
                    segments=results, audio_paths=list(audio_paths),
                    total_duration_sec=cursor, provider_name="edge_tts"
                )
        return asyncio.run(_synth())


class MacOSTTS(TTSProvider):
    """macOS say 命令 — 离线可用"""

    VOICES = {"female": "Tingting", "male_reported": "Reed"}

    def synthesize(self, segments: List[str], voice: str = "female") -> TTSSynthesis:
        speaker = self.VOICES.get(voice, voice)
        results = []
        audio_paths = []
        cursor = 0.0

        with _temp_workdir() as workdir:
            for i, text in enumerate(segments):
                aiff = os.path.join(workdir, f"seg_{i:03d}.aiff")
                wav = os.path.join(workdir, f"seg_{i:03d}.wav")
                subprocess.run(["say", "-v", speaker, text, "-o", aiff], capture_output=True)
                subprocess.run(
                    f'ffmpeg -y -i "{aiff}" -ar 44100 -ac 1 "{wav}"',
                    shell=True, capture_output=True
                )
                dur = float(subprocess.run(
                    f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{wav}"',
                    shell=True, capture_output=True, text=True
                ).stdout.strip() or "2.0")
                results.append(TTSSegment(text=text, audio_path=wav, start_sec=cursor, duration_sec=dur))
                audio_paths.append(wav)
                cursor += dur + 0.15

        return TTSSynthesis(
            segments=results, audio_paths=audio_paths,
            total_duration_sec=cursor, provider_name="macos_say",
        )


def auto_detect_tts() -> TTSProvider:
    skill_root = os.path.expanduser("~/.claude/skills/jianying-editor/scripts/jy_wrapper.py")
    if os.path.exists(skill_root):
        return SAMITTS()
    try:
        import edge_tts  # noqa: F401
        return EdgeTTS()
    except ImportError:
        pass
    if sys.platform == "darwin":
        return MacOSTTS()
    raise RuntimeError(
        "No TTS provider available. Options:\n"
        "  1. Install jianying-editor skill: git clone ... ~/.claude/skills/jianying-editor\n"
        "  2. pip install edge-tts\n"
        "  3. macOS users can use built-in 'say' command"
    )
