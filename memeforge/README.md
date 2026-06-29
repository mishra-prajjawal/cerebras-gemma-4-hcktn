# Meme Forge

Real-time AI writers' room on Gemma 4 + Cerebras. Drop an image; a swarm of comedian-agents
captions it in parallel; a judge ranks; you get share-ready memes in about a second.

## Quickstart
```bash
cp .env.example .env        # add only CEREBRAS_API_KEY
pip install -e .[dev]
python -m memeforge.app path/to/image.jpg "optional topic"
```

## Layout
- `src/memeforge/` - core (client, rate limiter, audit, config) + `agents/` + `pipeline.py`
- `personas.py` - the writers' room (edit to retune voices)
- `render.py` - caption overlay (TODO)
- `skills/` - the persistent know-how the build agent follows
- `CLAUDE.md` / `PROMPT.md` - agent guide + build prompt

Model access is the OpenAI-compatible Cerebras endpoint; only an API key is needed.
