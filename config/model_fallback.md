## Model Priority

1. **PRIMARY:** `ollama/kimi-k2.6:cloud` (current)
2. **FALLBACK:** `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter

## When to Use Fallback

- Ollama usage limit reached
- Ollama API errors or timeouts (>180s)
- Primary model unavailable
- GPU contention prevents Ollama responses

## OpenRouter Configuration

- **Base URL:** `https://openrouter.ai/api/v1`
- **Model:** `nvidia/nemotron-3-super-120b-a12b:free`
- **Auth:** Bearer token in `Authorization` header
- **API Key Source:** `config/secrets/openrouter.env` (not committed)

## Usage in OpenClaw

Set via gateway config or environment variable:
```bash
export OPENROUTER_API_KEY=$(cat config/secrets/openrouter.env | cut -d= -f2)
```

## Security

- API key is stored in `config/secrets/` (gitignored)
- Never commit keys to repository
- Rotate key if exposed
