# Red-Team Committee

Instant adversarial document review on Gemma 4 + Cerebras. A parallel committee (Legal, Risk,
Finance, Security) shreds a contract with cited findings; a chair returns a fail-closed verdict
in seconds.

## Quickstart
```bash
cp .env.example .env        # add only CEREBRAS_API_KEY
pip install -e .[dev]
python -m redteam.app path/to/contract.txt
```

## Layout
- `src/redteam/` - core + `agents/` (reviewer, moderator, vision_reader STUB) + `pipeline.py`
- `roles.py` - the committee (edit to add reviewer roles)
- `ingest.py` - bounded text clipping
- `skills/` - persistent know-how; `CLAUDE.md` / `PROMPT.md` - agent guide + build prompt

Grounding is enforced in code: findings without a verbatim citation are dropped. Model access
is the OpenAI-compatible Cerebras endpoint; only an API key is needed.
