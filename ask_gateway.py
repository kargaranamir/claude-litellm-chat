# /// script
# requires-python = ">=3.9"
# dependencies = ["anthropic>=0.40"]
# ///
"""
Multi-turn chat against the LiteLLM gateway, using the exact endpoint and
API key configured in Claude Code's settings.json.

Run with:   uv run ask_gateway.py
Switch model: uv run ask_gateway.py --model claude-sonnet-4-6
List models:  uv run ask_gateway.py --list-models

Everything below is split into small functions so you can edit each piece
independently (config loading, client creation, asking, the conversation).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from anthropic import Anthropic

# --------------------------------------------------------------------------
# Config — read endpoint, key and model defaults straight from settings.json
# --------------------------------------------------------------------------

# Search order for the settings file (first one that exists wins).
SETTINGS_PATHS = [
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
]


def load_settings() -> dict:
    """Return the `env` block from the first settings.json that exists."""
    for path in SETTINGS_PATHS:
        if path.is_file():
            with path.open() as fh:
                data = json.load(fh)
            return data.get("env", {})
    raise FileNotFoundError(
        f"No settings file found in: {', '.join(map(str, SETTINGS_PATHS))}"
    )


def get_config() -> dict:
    """
    Resolve the values we need. A real environment variable always wins over
    the settings.json value, so you can override on the command line, e.g.
        ANTHROPIC_BASE_URL=... uv run ask_gateway.py
    """
    env = load_settings()

    def pick(key: str, default: str | None = None) -> str | None:
        return os.environ.get(key) or env.get(key) or default

    return {
        "base_url": pick("ANTHROPIC_BASE_URL"),
        "api_key": pick("ANTHROPIC_API_KEY"),
        "default_model": pick("ANTHROPIC_DEFAULT_OPUS_MODEL", "claude-opus-4-8"),
    }


# --------------------------------------------------------------------------
# Client + a single ask
# --------------------------------------------------------------------------


def make_client(cfg: dict) -> Anthropic:
    """Build an Anthropic-compatible client pointed at the gateway."""
    return Anthropic(api_key=cfg["api_key"], base_url=cfg["base_url"])


def ask(client: Anthropic, model: str, messages: list[dict], max_tokens: int = 512) -> str:
    """
    Send the full message history and return the assistant's text reply.
    `messages` is the running conversation; we don't mutate it here.
    """
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    )
    # Concatenate any text blocks in the response.
    return "".join(block.text for block in resp.content if block.type == "text")


def ask_stream(client: Anthropic, model: str, messages: list[dict], max_tokens: int = 512) -> str:
    """
    Same as ask(), but prints each text delta as it arrives and returns the
    full reply at the end. Set STREAM = False in run_conversation to disable.
    """
    text = ""
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
    ) as stream:
        for delta in stream.text_stream:
            print(delta, end="", flush=True)
            text += delta
    print()  # trailing newline after the streamed reply
    return text


def list_models(client: Anthropic) -> list[str]:
    """Ask the gateway which models it serves."""
    return [m.id for m in client.models.list().data]


# --------------------------------------------------------------------------
# The actual conversation — edit the turns here
# --------------------------------------------------------------------------


# Set to False to get the whole reply at once instead of streaming token-by-token.
STREAM = True


def run_conversation(client: Anthropic, model: str) -> None:
    print(f"# model: {model}\n")

    say = ask_stream if STREAM else ask

    # Start with an empty history and build it up turn by turn.
    history: list[dict] = []

    # ---- Turn 1 -----------------------------------------------------------
    history.append({"role": "user", "content": "What is the capital of Germany?"})
    print("Q1: What is the capital of Germany?")
    print("A1: ", end="" if STREAM else None)
    answer1 = say(client, model, history)
    history.append({"role": "assistant", "content": answer1})
    print()

    # ---- Turn 2 (continues the same history) ------------------------------
    history.append({"role": "user", "content": "How about France?"})
    print("Q2: How about France?")
    print("A2: ", end="" if STREAM else None)
    answer2 = say(client, model, history)
    history.append({"role": "assistant", "content": answer2})


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> None:
    cfg = get_config()

    parser = argparse.ArgumentParser(description="Chat with the LiteLLM gateway.")
    parser.add_argument(
        "--model",
        default=cfg["default_model"],
        help=f"Model id to use (default: {cfg['default_model']})",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Print the models the gateway serves, then exit.",
    )
    args = parser.parse_args()

    client = make_client(cfg)

    if args.list_models:
        for model_id in list_models(client):
            print(model_id)
        return

    run_conversation(client, args.model)


if __name__ == "__main__":
    main()
