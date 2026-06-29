# Build info (verified against live docs, Jun 2026)

- **Endpoint**: OpenAI-compatible Cerebras API, base_url `https://api.cerebras.ai/v1`.
  Use the official `openai` Python SDK (`AsyncOpenAI`) as a drop-in. (Cerebras docs:
  /resources/openai; confirmed fully OpenAI-compatible.)
- **Model**: `gemma-4-31b` (hackathon id; override via `MODEL_ID` env if the event differs).
  Text + image in, text out. No audio. 5K max sequence / 32K max context.
- **Auth**: only `CEREBRAS_API_KEY` required at runtime. `CEREBRAS_BASE_URL` + `MODEL_ID`
  have safe defaults in every `config.py` and `.env.example`.
- **Limits**: 100 RPM / 100K TPM, enforced by the shared token-bucket `rate_limiter.py`.
- **Structured outputs**: strict mode, `response_format` json_schema with `strict:true` and
  `additionalProperties:false` on EVERY object. Schema is generated from the Pydantic model.
- **Cerebras-only params** (e.g. `reasoning_effort`) are passed via the SDK `extra_body`.
- **API version**: behavior matches v1; Cerebras makes v2 (stricter validation) the default
  2026-07-21 - these kits already satisfy v2's schema rules.
- **SDKs**: pinned loosely (`openai>=1.40`, `pydantic>=2.7`); run `pip install -e .[dev]` to
  resolve current versions at build time.
