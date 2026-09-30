"""Shared Anthropic client construction for `llm_client.ClaudeClient` and
`assistant.PlatformAssistant`.

Both wrap the Anthropic API and both need the same live/mock decision: resolve
credentials from `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` (the anthropic
SDK reads these itself when not passed explicitly), or fall back to `None` so
the caller can run its own deterministic mock path — either because the
caller passed `force_mock=True`, no credentials are set, or the `anthropic`
package isn't installed.
"""

from __future__ import annotations

import os


def resolve_client(api_key: str | None = None, force_mock: bool = False):
    """Returns a live `anthropic.Anthropic` client, or `None` for mock mode."""
    if force_mock:
        return None

    resolved_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    resolved_auth_token = None if resolved_api_key else os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not (resolved_api_key or resolved_auth_token):
        return None

    try:
        import anthropic
    except ImportError:
        return None

    return anthropic.Anthropic(api_key=resolved_api_key, auth_token=resolved_auth_token)
