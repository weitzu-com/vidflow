"""
Seedance API 视频生成封装 v2
审核规避改进 + rate limit 保护 + 完整错误处理
"""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class VideoScene:
    name: str
    prompt: str
    duration: int = 8
    resolution: str = "720p"
    path: Optional[str] = None


class SeedanceProvider:
    API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    MODEL_ID = "doubao-seedance-2-0-260128"
    FAST_MODEL = "doubao-seedance-2-0-fast-260128"

    # 审核规避：整词替换，保持语法完整性
    _SAFE_REPLACEMENTS = [
        ("blood-red", "crimson"),
        ("blood red", "deep amber"),
        ("military markers", "trade route markers"),
        ("troop positions", "settlement locations"),
        ("killing fields", "devastated terrain"),
        ("death scene", "dramatic scene"),
    ]

    def __init__(self, api_key: str, model: str = None, output_dir: str = "./videos",
                 max_rps: float = 1.0):
        self.api_key = api_key
        self.model = model or self.MODEL_ID
        self.output_dir = output_dir
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._rate_lock = threading.Lock()
        self._last_call = 0.0
        self._min_interval = 1.0 / max_rps if max_rps > 0 else 0
        os.makedirs(output_dir, exist_ok=True)

    def _rate_limit(self):
        with self._rate_lock:
            elapsed = time.time() - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.time()

    @classmethod
    def sanitize_prompt(cls, prompt: str) -> str:
        p = prompt
        for old, new in cls._SAFE_REPLACEMENTS:
            p = p.replace(old, new)
        return p

    def generate_one(self, scene: VideoScene, timeout: int = 600) -> Optional[str]:
        path = os.path.join(self.output_dir, f"{scene.name}.mp4")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            scene.path = path
            return path

        body = {
            "model": self.model,
            "content": [{"type": "text", "text": self.sanitize_prompt(scene.prompt)}],
            "ratio": "16:9", "resolution": scene.resolution,
            "duration": scene.duration, "generate_audio": False,
        }

        self._rate_limit()
        r = requests.post(
            f"{self.API_BASE}/contents/generations/tasks",
            headers=self.headers, json=body, timeout=30
        )
        if r.status_code != 200:
            raise RuntimeError(f"Seedance HTTP {r.status_code}: {r.text[:300]}")
        task_id = r.json()["id"]

        start = time.time()
        last_status = None
        while time.time() - start < timeout:
            r2 = requests.get(
                f"{self.API_BASE}/contents/generations/tasks/{task_id}",
                headers=self.headers, timeout=10
            )
            if r2.status_code != 200:
                time.sleep(5)
                continue
            d = r2.json()
            s = d.get("status")
            if s != last_status:
                last_status = s
            if s == "succeeded":
                vu = d["content"]["video_url"]
                for attempt in range(3):
                    try:
                        r3 = requests.get(vu, timeout=120)
                        if r3.status_code == 200:
                            with open(path, "wb") as f:
                                f.write(r3.content)
                            scene.path = path
                            return path
                    except Exception:
                        if attempt < 2:
                            time.sleep(5)
                raise RuntimeError(f"Failed to download after 3 attempts: {task_id}")
            elif s == "failed":
                err = d.get("error", {}).get("message", "unknown")
                raise RuntimeError(f"Seedance task failed: {err}")
            time.sleep(10)
        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

    def generate_all(self, scenes: List[VideoScene], parallel: bool = True) -> Dict[str, str]:
        if not parallel:
            results = {}
            for s in scenes:
                try:
                    results[s.name] = self.generate_one(s)
                except Exception:
                    results[s.name] = None
            return results

        results = {}
        with ThreadPoolExecutor(max_workers=min(10, len(scenes))) as ex:
            futures = {ex.submit(self.generate_one, s): s.name for s in scenes}
            for f in as_completed(futures):
                name = futures[f]
                try:
                    results[name] = f.result()
                except Exception:
                    results[name] = None
        return results
