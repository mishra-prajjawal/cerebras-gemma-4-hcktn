# Cerebras x Gemma 4 Hackathon - Build Kits

Three self-contained, agent-ready repos. Each is locked, complete, and runs on the
**OpenAI-compatible Cerebras endpoint** - the only thing you add is your API key.

| Dir | Track | Idea |
|-----|-------|------|
| `reflex/`    | 1 - Multiverse Agents | REFLEX: real-time embodied build copilot (vision agent swarm) |
| `memeforge/` | 2 - People's Choice   | Meme Forge: real-time AI writers' room (parallel comedian agents + judge) |
| `redteam/`   | 3 - Enterprise Impact | Red-Team Committee: instant adversarial document review with cited findings |

## Each kit contains
- `CLAUDE.md` - persistent guide the coding agent reads every session
- `PROMPT.md` - the build prompt to hand the coding agent
- `skills/` - the know-how (Cerebras inference, strict outputs, vision, orchestration,
  NASA Power of 10, audited I/O) plus track-specific skills
- `src/<pkg>/` - NASA-grade async skeleton: strict typed contracts, audited steps, rate
  limiter, shared OpenAI-compatible client, agents, orchestrator/pipeline
- `tests/` - contract tests; `pyproject.toml`, `.env.example`, `.gitignore`

## Run any kit
```bash
cd <kit>
cp .env.example .env      # add ONLY CEREBRAS_API_KEY
pip install -e .[dev]
pytest -q
```

See `BUILD_INFO.md` for the exact model/endpoint/SDK facts.
