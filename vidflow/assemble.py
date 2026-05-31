"""
FFmpeg 视频合成引擎 v2
唯一临时目录 + 空视频回退 + 异常安全清理
"""
import os, subprocess, tempfile, shutil
from typing import List, Optional, Tuple


def _find_ffmpeg() -> str:
    for c in ["/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"]:
        try:
            r = subprocess.run(
                f'{c} -filters 2>&1', shell=True, capture_output=True, text=True, timeout=10
            )
            if 'subtitles' in r.stdout:
                return c
        except Exception:
            continue
    raise RuntimeError(
        "FFmpeg with libass not found.\n"
        "  macOS: brew install ffmpeg-full\n"
        "  Linux: apt install ffmpeg\n"
        "  Verify: ffmpeg -filters 2>&1 | grep subtitles"
    )


def _dur(path: str) -> float:
    ffprobe = _find_ffmpeg().replace("ffmpeg", "ffprobe")
    try:
        r = subprocess.run(
            f'{ffprobe} -v error -show_entries format=duration '
            f'-of default=noprint_wrappers=1:nokey=1 "{path}"',
            shell=True, capture_output=True, text=True, timeout=30
        )
        val = r.stdout.strip()
        return float(val) if val else 5.0
    except Exception:
        return 5.0


def _fmt_srt(seconds: float) -> str:
    h, m = int(seconds // 3600), int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


COLOR_STYLES = {
    "dark_cinematic": {"brightness": -0.06, "contrast": 1.15, "saturation": 0.75},
    "warm_documentary": {"brightness": 0.0, "contrast": 1.05, "saturation": 0.9},
    "none": {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0},
}


class FFmpegAssembler:
    def __init__(self, ffmpeg_path: str = None):
        self.ffmpeg = ffmpeg_path or _find_ffmpeg()

    def assemble(
        self, video_paths: List[str], audio_paths: List[str],
        subtitles: List[Tuple[float, float, str]], output_path: str,
        bgm_path: str = None, color_style: str = "dark_cinematic",
        total_audio_dur: float = None, width: int = 1920, height: int = 1080,
    ) -> str:
        ffmpeg = self.ffmpeg
        workdir = tempfile.mkdtemp(prefix="vidflow_assemble_")
        cs = COLOR_STYLES.get(color_style, COLOR_STYLES["dark_cinematic"])

        try:
            # 1. concat 音频
            full_audio = os.path.join(workdir, "full_audio.ogg")
            if audio_paths:
                alist = os.path.join(workdir, "alist.txt")
                with open(alist, "w") as f:
                    for af in audio_paths:
                        d = _dur(af)
                        f.write(f"file '{af}'\nduration {d:.3f}\n")
                subprocess.run(
                    f'{ffmpeg} -y -f concat -safe 0 -i "{alist}" -c copy "{full_audio}"',
                    shell=True, capture_output=True, timeout=120
                )

            # 2. concat 视频 / 生成黑幕回退
            merged_v = os.path.join(workdir, "merged.mp4")
            if video_paths:
                vlist = os.path.join(workdir, "vlist.txt")
                with open(vlist, "w") as f:
                    for vp in video_paths:
                        f.write(f"file '{vp}'\n")
                subprocess.run(
                    f'{ffmpeg} -y -f concat -safe 0 -i "{vlist}" -c copy "{merged_v}"',
                    shell=True, capture_output=True, timeout=120
                )
            else:
                fallback_dur = total_audio_dur or 60.0
                subprocess.run(
                    f'{ffmpeg} -y -f lavfi -i color=c=0x0a0a0a:s={width}x{height}:d={fallback_dur:.1f}:r=25 '
                    f'-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p "{merged_v}"',
                    shell=True, capture_output=True, timeout=120
                )

            # 3. 时长
            vdur = _dur(merged_v)
            adur = _dur(full_audio) if total_audio_dur is None else total_audio_dur
            if audio_paths and not total_audio_dur:
                adur = _dur(full_audio)
            elif not audio_paths:
                adur = vdur
            total = max(vdur, adur)
            pad = max(0, total - vdur)
            has_bgm = bgm_path and os.path.exists(bgm_path)

            # 4. 第一遍编码
            temp = os.path.join(workdir, "temp.mp4")
            has_audio = audio_paths and os.path.exists(full_audio)

            if has_audio and has_bgm:
                filt = (
                    f'[0:v]tpad=stop_mode=clone:stop_duration={pad:.1f},'
                    f'eq=brightness={cs["brightness"]}:contrast={cs["contrast"]}:saturation={cs["saturation"]}[v];'
                    f'[2:a]atrim=0:{total:.1f},volume=0.10[bgm];[1:a][bgm]amix=inputs=2:duration=first[a]'
                )
                subprocess.run(
                    f'{ffmpeg} -y -i "{merged_v}" -i "{full_audio}" -i "{bgm_path}" '
                    f'-filter_complex "{filt}" -map "[v]" -map "[a]" '
                    f'-c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p "{temp}"',
                    shell=True, capture_output=True, timeout=300
                )
            elif has_audio:
                filt = (
                    f'[0:v]tpad=stop_mode=clone:stop_duration={pad:.1f},'
                    f'eq=brightness={cs["brightness"]}:contrast={cs["contrast"]}:saturation={cs["saturation"]}[v]'
                )
                subprocess.run(
                    f'{ffmpeg} -y -i "{merged_v}" -i "{full_audio}" '
                    f'-filter_complex "{filt}" -map "[v]" -map 1:a '
                    f'-c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p "{temp}"',
                    shell=True, capture_output=True, timeout=300
                )
            else:
                subprocess.run(
                    f'{ffmpeg} -y -i "{merged_v}" '
                    f'-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p "{temp}"',
                    shell=True, capture_output=True, timeout=300
                )

            # 5. 烧录字幕
            if subtitles and os.path.exists(temp):
                srt = os.path.join(workdir, "subs.srt")
                with open(srt, "w", encoding="utf-8") as f:
                    for i, (s, e, t) in enumerate(subtitles, 1):
                        f.write(f"{i}\n{_fmt_srt(s)} --> {_fmt_srt(e)}\n{t}\n\n")
                subprocess.run(
                    f'{ffmpeg} -y -i "{temp}" -vf subtitles="{srt}" '
                    f'-c:v libx264 -preset slow -crf 18 -c:a copy "{output_path}"',
                    shell=True, capture_output=True, timeout=300
                )
            else:
                os.rename(temp, output_path)

        finally:
            shutil.rmtree(workdir, ignore_errors=True)

        return output_path if os.path.exists(output_path) else ""
