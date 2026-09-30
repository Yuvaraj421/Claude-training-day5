"""Wraps the Anthropic API for clinical note drafting.

Doc reference: 01-banner-health-clinical-documentation.md, component
"Clinical LLM Drafting Service" ("LLM (e.g., Claude) with clinical prompt templates").

Resolves credentials from either ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN
(+ optional ANTHROPIC_BASE_URL for an API-compatible proxy) — the anthropic SDK
reads these environment variables itself when not passed explicitly. If neither
is set, or the API call fails, falls back to a deterministic templated note so
the demo still runs end-to-end offline.
"""

from __future__ import annotations

import json
import os
import re

MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT = """You are a clinical documentation assistant. Given a visit transcript and a \
condensed patient history, draft a structured SOAP note. Respond ONLY with a JSON object with \
exactly these string keys: "subjective", "objective", "assessment", "plan". Be concise and \
clinically appropriate. Do not invent findings that are not supported by the transcript or history."""


class ClaudeClient:
    def __init__(self, api_key: str | None = None, force_mock: bool = False):
        self._client = None
        if force_mock:
            return

        resolved_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        resolved_auth_token = None if resolved_api_key else os.environ.get("ANTHROPIC_AUTH_TOKEN")
        if resolved_api_key or resolved_auth_token:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=resolved_api_key, auth_token=resolved_auth_token)
            except ImportError:
                self._client = None

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def generate_note(self, transcript_text: str, history_summary: str) -> tuple[dict, str]:
        """Returns (sections_dict, generated_by) where generated_by is 'llm' or 'mock'."""
        if self._client is not None:
            try:
                return self._generate_live(transcript_text, history_summary), "llm"
            except Exception:
                pass  # fall through to mock
        return self._generate_mock(transcript_text, history_summary), "mock"

    def _generate_live(self, transcript_text: str, history_summary: str) -> dict:
        user_content = (
            f"Patient history:\n{history_summary}\n\nVisit transcript:\n{transcript_text}"
        )
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text")
        return self._parse_sections(raw_text)

    @staticmethod
    def _parse_sections(raw_text: str) -> dict:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        payload = json.loads(match.group(0) if match else raw_text)
        return {
            "subjective": payload.get("subjective", ""),
            "objective": payload.get("objective", ""),
            "assessment": payload.get("assessment", ""),
            "plan": payload.get("plan", ""),
        }

    @staticmethod
    def _generate_mock(transcript_text: str, history_summary: str) -> dict:
        """Deterministic templated note used when no live LLM is available."""
        return {
            "subjective": f"Patient reports: {transcript_text.strip()}",
            "objective": "Vitals and exam findings as documented during the encounter.",
            "assessment": (
                "Findings reviewed in the context of the patient's known history:\n"
                f"{history_summary}"
            ),
            "plan": (
                "[MOCK MODE — set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN for AI-generated plan] "
                "Continue current management; follow up as clinically indicated."
            ),
        }
