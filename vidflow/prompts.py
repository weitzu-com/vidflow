"""
提示词模板库 — 暗黑史诗 / 温暖纪录片 / 科技感 / 古风
"""
from typing import Dict

PROMPT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "dark_cinematic": {
        "palace": (
            "Ancient Chinese imperial palace interior at twilight, ornate golden decorations, "
            "empty throne, silk curtains moving in breeze, single candle flickering, "
            "dark cinematic lighting, deep shadows, melancholic atmosphere, wide shot"
        ),
        "battle": (
            "Ancient battlefield viewed from high vantage point, scattered armor and broken "
            "banners under storm clouds, smoke columns rising in distance, no visible figures, "
            "dark atmospheric cinematography, desaturated earth tones, epic scale shot"
        ),
        "map": (
            "Aged parchment map illuminated by single candle from side, ink lines showing "
            "ancient trade routes, deep shadows swallowing edges, warm amber light on center, "
            "contemplative atmosphere, shallow depth of field, cinematic still life"
        ),
        "ruins": (
            "Ruined ancient stone archways silhouetted against dying sunset, overgrown with "
            "dead vines, ash particles floating in last rays of light, profound silence, "
            "dark atmospheric cinematography, almost monochrome with subtle warm undertones"
        ),
        "ending": (
            "Ancient scroll slowly burning from edges, embers floating upward into darkness, "
            "last traces of calligraphy fading to ash, philosophical and timeless, "
            "minimal light, profound darkness, meditation on impermanence"
        ),
        "split_screen": (
            "Split screen composition: left half shows opulent golden palace interior with "
            "silk curtains blowing gently, right half shows desolate battlefield under storm "
            "clouds, dramatic contrast, dark cinematic lighting, film grain texture"
        ),
        "cavalry": (
            "Massive ancient cavalry charging through dark storm, silhouettes against lightning, "
            "dust clouds illuminated by brief flashes, war banners torn by wind, "
            "dark epic cinematic shot, desaturated colors with deep blacks, atmospheric haze"
        ),
        "night_escape": (
            "Ancient procession fleeing through narrow mountain pass in complete darkness, "
            "single line of torches barely visible through heavy rain, dark moody night "
            "cinematography, minimal lighting, silhouettes against faint moonlight"
        ),
    },
    "warm_documentary": {
        "palace": "Ancient Chinese palace in warm golden sunlight, peaceful atmosphere, documentary style, medium shot",
        "battle": "Historical battlefield at sunrise, soft golden light, respectful distance, documentary wide shot",
        "ruins": "Ancient ruins with wildflowers growing through stones, warm afternoon light, hopeful documentary tone",
    },
}

STYLE_MODIFIERS = {
    "dark_cinematic": (
        "dark cinematic lighting, deep shadows, moody atmosphere, atmospheric haze, "
        "high contrast, desaturated colors with deep blacks, film grain texture, "
        "cinematic wide shot, epic historical documentary aesthetic"
    ),
    "warm_documentary": (
        "warm natural lighting, soft shadows, gentle atmosphere, "
        "moderate contrast, natural colors, documentary style, educational tone"
    ),
    "tech_futuristic": (
        "clean modern lighting, neon accents, sleek surfaces, "
        "high tech atmosphere, blue and purple color palette, cinematic product shot"
    ),
    "ancient_chinese": (
        "traditional Chinese ink wash painting aesthetic, soft brushstroke textures, "
        "muted earth tones, negative space composition, classical Chinese art style"
    ),
}


def apply_style(base_prompt: str, style: str = "dark_cinematic") -> str:
    """给基础提示词附加风格修饰"""
    modifier = STYLE_MODIFIERS.get(style, "")
    return f"{base_prompt}, {modifier}" if modifier else base_prompt


def get_scene_prompt(scene_type: str, style: str = "dark_cinematic") -> str:
    """获取特定场景类型的提示词模板"""
    templates = PROMPT_TEMPLATES.get(style, PROMPT_TEMPLATES["dark_cinematic"])
    return templates.get(scene_type, templates.get("palace", ""))
