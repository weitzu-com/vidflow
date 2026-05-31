# Security Policy

## Reporting a Vulnerability

Do NOT open a public issue. Email the maintainers directly.

## API Key Security

- vidflow reads API keys from environment variable `ARK_API_KEY` only
- Never hardcode API keys in source code
- Never commit `.env` files
- The `.gitignore` excludes common secret patterns

## Dependency Scanning

CI runs `bandit` on every push. Run locally:

```bash
pip install bandit
bandit -r vidflow/ -ll
```

## Supported Versions

| Version | Supported |
|---------|----------|
| 0.1.x   | Yes      |

## Third-Party Services

| Service | Data Sent | Privacy |
|---------|----------|---------|
| Seedance API (Volcengine ARK) | Video generation prompts | Per Volcengine ToS |
| SAMI TTS (JianYing) | Narration text | Per JianYing ToS |
| edge-tts (Microsoft) | Narration text | Per Microsoft ToS |
