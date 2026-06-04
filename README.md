# claude-litellm-chat

A tiny, single-file CLI that holds a multi-turn conversation with a [LiteLLM](https://github.com/BerriAI/litellm) gateway — reusing the endpoint and API key already configured in your Claude Code `settings.json`, so there's nothing extra to set up.

## Why

If you already use Claude Code against a LiteLLM gateway, your endpoint and key live in `~/.claude/settings.json`. This script just borrows them — no `.env`, no hardcoded secrets.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) (`brew install uv`)
- A `~/.claude/settings.json` with an `env` block containing `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY`

Python deps are declared inline (PEP 723) at the top of the script, so `uv` installs them automatically on first run.

## Usage

```bash
uv run ask_gateway.py                            # streamed chat, default model
uv run ask_gateway.py --model claude-sonnet-4-6  # pick any model the gateway serves
uv run ask_gateway.py --list-models              # ask the gateway what's available
```

## How it works

- Reads the `env` block from `~/.claude/settings.json` (falls back to `settings.local.json`); a real environment variable overrides the settings value.
- Builds the conversation in a single `history` list, so each turn sees the previous ones.
- Streams tokens as they arrive (toggle `STREAM = False` for single-shot replies).

## Editing

Functions are kept small and separate so you can change one piece at a time:

| Function | Does |
|---|---|
| `load_settings` / `get_config` | Resolve endpoint, key, default model |
| `make_client` | Build the Anthropic-compatible client |
| `ask` / `ask_stream` | One request (buffered / streamed) |
| `list_models` | Query available models |
| `run_conversation` | The actual turns — edit your questions here |

## License

Apache 2.0
