# Changelog

## [0.1.0] — 2026-05-31

### Added
- Initial release: vidflow SDK for AI short video production
- Five-stage pipeline: Script → Seedance Video → TTS → FFmpeg Assembly → Output
- TTS providers: SAMITTS (JianYing), EdgeTTS (Microsoft), MacOSTTS (macOS say)
- Video provider: Seedance API v2.0 with parallel generation
- FFmpeg assembler with dark cinematic color grading, BGM mixing, subtitle burning
- Prompt template library: dark_cinematic, warm_documentary, tech_futuristic, ancient_chinese
- 6 dark cinematic scene templates (palace, battle, map, ruins, ending, split_screen, cavalry, night_escape)
- Content safety filter for Seedance prompts
- CI/CD pipeline: pytest + ruff + bandit + build
- Complete example: An-Shi Rebellion historical short video
