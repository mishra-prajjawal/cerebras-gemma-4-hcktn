# REFLEX — real-time embodied build/repair copilot (Track 1)

A webcam watches your workbench; a 5-agent swarm on **gemma-4-31b @ Cerebras** catches
mistakes within ~1s and speaks the fix. Multi-agent + multimodal + physical-AI bonus.

## Quickstart
```bash
cp .env.example .env   # add your CEREBRAS_API_KEY
pip install -e ".[dev]"
pytest -q
python -m reflex.app
```

## Layout
- `CLAUDE.md` — persistent guide (read first). `PROMPT.md` — paste to your coding agent.
- `skills/` — reference manuals. `src/reflex/` — typed, audited, rate-limited engine.
- Hot path: frames -> perceptor -> state_tracker -> error_sentinel -> coach -> narrator.

Stubs raise NotImplementedError with TODO(agent) — that is the build surface.
