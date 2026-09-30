"""Wraps the Anthropic API for tenant-templated clinical note generation.

Doc reference: 05-commure-clinical-documentation-automation.md, component
"LLM Documentation Service Pool" ("Generates structured notes per tenant's
template/specialty", "Auto-scaled LLM inference pool, per-tenant prompt
configs") and key processing step #3 ("Resolve tenant-specific note templates
and specialty vocabulary at generation time so one shared LLM service pool
can serve heterogeneous health systems").

Unlike a single-tenant drafter with a fixed SOAP schema, the section list is
supplied per call from the tenant's `NoteTemplate` — the same LLM pool serves
every tenant's specialty/section shape via prompt injection.

Resolves credentials from either ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN
(+ optional ANTHROPIC_BASE_URL for an API-compatible proxy) — the anthropic
SDK reads these environment variables itself when not passed explicitly. If
neither is set, or the API call fails, falls back to a deterministic
templated note so the demo still runs end-to-end offline.
"""

from __future__ import annotations

import json
import re

from anthropic_client import resolve_client

MODEL = "claude-sonnet-5"

_SYSTEM_PROMPT_TEMPLATE = """You are a clinical documentation assistant generating a note for the \
specialty "{specialty}". Given an encounter transcript, draft a structured clinical note. Respond \
ONLY with a JSON object whose keys are exactly this list, in any order: {sections}. Be concise and \
clinically appropriate. Do not invent findings that are not supported by the transcript."""


class ClaudeClient:
    def __init__(self, api_key: str | None = None, force_mock: bool = False):
        self._client = resolve_client(api_key, force_mock)

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def generate_note(self, transcript_text: str, section_schema: list[str], specialty: str) -> tuple[dict, str]:
        """Returns (content_sections, generated_by) where generated_by is 'llm' or 'mock'."""
        if self._client is not None:
            try:
                return self._generate_live(transcript_text, section_schema, specialty), "llm"
            except Exception:
                pass  # fall through to mock
        return self._generate_mock(transcript_text, section_schema), "mock"

    def _generate_live(self, transcript_text: str, section_schema: list[str], specialty: str) -> dict:
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(specialty=specialty, sections=section_schema)
        response = self._client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Encounter transcript:\n{transcript_text}"}],
        )
        raw_text = "".join(block.text for block in response.content if block.type == "text")
        return self._parse_sections(raw_text, section_schema)

    @staticmethod
    def _parse_sections(raw_text: str, section_schema: list[str]) -> dict:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        payload = json.loads(match.group(0) if match else raw_text)
        return {section: payload.get(section, "") for section in section_schema}

    @staticmethod
    def _generate_mock(transcript_text: str, section_schema: list[str]) -> dict:
        """Deterministic templated note used when no live LLM is available."""
        sections = {}
        for i, section in enumerate(section_schema):
            if i == 0:
                sections[section] = f"[MOCK MODE] Encounter transcript: {transcript_text.strip()}"
            elif i == len(section_schema) - 1:
                sections[section] = (
                    "[MOCK MODE — set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN for AI-generated content] "
                    "Continue current management; follow up as clinically indicated."
                )
            else:
                sections[section] = f"[MOCK MODE] {section.replace('_', ' ').capitalize()} pending clinician review."
        return sections
