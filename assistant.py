"""Conversational operations assistant over the multi-tenant pipeline.

Doc reference: 05-commure-clinical-documentation-automation.md describes a
platform-operator surface (dashboard/API) for onboarding tenants, configuring
templates, and monitoring throughput. This module adds a chat-driven front
end onto that same surface: instead of clicking through tabs, an operator can
ask "how is Riverside doing?" or "submit a cardiology encounter for Lakeshore
saying ..." and the assistant resolves it to calls on the same
`orchestrator.MultiTenantPipeline` the dashboard and API already use.

Like `llm_client.ClaudeClient`, this falls back to a deterministic command
parser when no live Anthropic credentials are available, so the chat tab
still works end-to-end offline — it just trades free-form language for a
handful of recognized commands.
"""

from __future__ import annotations

import json
import re

from anthropic_client import resolve_client
from models import EHRVendor

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are the operations assistant for a multi-tenant clinical \
documentation automation platform (ambient dictation -> ASR -> LLM-drafted note -> \
EHR delivery, per health-system tenant). You help a platform operator look up \
tenants, onboard new ones, configure per-specialty note templates, submit \
encounters, and check throughput/latency metrics — entirely through the tools \
provided. Always resolve a tenant the user names to one from `list_tenants` \
before acting; if the name is ambiguous or not found, ask which tenant they \
meant rather than guessing. This is an educational demo with synthetic data — \
never imply you are accessing a real patient record or a real health system's \
production EHR. Keep answers concise and concrete (cite tenant names, specialties, \
counts, and IDs from tool results rather than vague summaries)."""

TOOLS = [
    {
        "name": "list_tenants",
        "description": "List all onboarded tenants with their EHR vendor, region, and configured specialties.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_metrics",
        "description": "Get throughput/latency metrics (captured, transcribed, notes generated, delivered, avg ASR latency) for one tenant.",
        "input_schema": {
            "type": "object",
            "properties": {"tenant": {"type": "string", "description": "Tenant name (or id)"}},
            "required": ["tenant"],
        },
    },
    {
        "name": "list_encounters",
        "description": "List recent encounters for one tenant, with status and EHR document id if delivered.",
        "input_schema": {
            "type": "object",
            "properties": {"tenant": {"type": "string", "description": "Tenant name (or id)"}},
            "required": ["tenant"],
        },
    },
    {
        "name": "get_note",
        "description": "Get the generated note sections and EHR delivery result for one encounter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tenant": {"type": "string", "description": "Tenant name (or id)"},
                "encounter_id": {"type": "string", "description": "Full or short (8-char) encounter id"},
            },
            "required": ["tenant", "encounter_id"],
        },
    },
    {
        "name": "register_tenant",
        "description": "Onboard a new health-system tenant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "health_system_name": {"type": "string"},
                "ehr_vendor": {"type": "string", "enum": [v.value for v in EHRVendor]},
                "data_residency_region": {"type": "string"},
            },
            "required": ["health_system_name", "ehr_vendor", "data_residency_region"],
        },
    },
    {
        "name": "set_template",
        "description": "Add or update a tenant's per-specialty note section schema (ordered list of section names).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tenant": {"type": "string", "description": "Tenant name (or id)"},
                "specialty": {"type": "string"},
                "section_schema": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["tenant", "specialty", "section_schema"],
        },
    },
    {
        "name": "submit_encounter",
        "description": "Submit a new encounter (dictation text) for a tenant and run it through the full pipeline (ASR -> LLM drafting -> EHR delivery).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tenant": {"type": "string", "description": "Tenant name (or id)"},
                "clinician_id": {"type": "string"},
                "specialty": {"type": "string"},
                "audio_text": {"type": "string", "description": "The dictated encounter text (stand-in for ambient audio)"},
            },
            "required": ["tenant", "clinician_id", "specialty", "audio_text"],
        },
    },
]


def _require_tenant(pipeline, name_or_id: str):
    """Raises with a message the model can act on (e.g. call list_tenants and
    retry) rather than a bare KeyError, since this runs inside a tool call."""
    tenant = pipeline.tenant_store.find_tenant(name_or_id)
    if tenant is None:
        raise ValueError(f"No tenant matching '{name_or_id}'. Call list_tenants to see options.")
    return tenant


def _tool_list_tenants(pipeline, tool_input: dict) -> dict:
    tenants = pipeline.tenant_store.list_tenants()
    return {
        "tenants": [
            {
                "id": t.id,
                "health_system_name": t.health_system_name,
                "ehr_vendor": t.ehr_vendor.value,
                "data_residency_region": t.data_residency_region,
                "specialties": list(t.note_templates.keys()),
            }
            for t in tenants
        ]
    }


def _tool_get_metrics(pipeline, tool_input: dict) -> dict:
    tenant = _require_tenant(pipeline, tool_input["tenant"])
    m = pipeline.get_metrics(tenant.id)
    return {
        "tenant": tenant.health_system_name,
        "encounters_captured": m.encounters_captured,
        "transcripts_completed": m.transcripts_completed,
        "notes_generated": m.notes_generated,
        "encounters_delivered": m.encounters_delivered,
        "avg_asr_latency_ms": m.avg_asr_latency_ms,
    }


def _tool_list_encounters(pipeline, tool_input: dict) -> dict:
    tenant = _require_tenant(pipeline, tool_input["tenant"])
    rows = []
    for e in pipeline.encounter_store.encounters_for_tenant(tenant.id):
        note = pipeline.get_note(tenant.id, e.id)
        rows.append(
            {
                "encounter_id": e.id,
                "short_id": e.id[:8],
                "clinician_id": e.clinician_id,
                "specialty": e.specialty,
                "status": e.status.value,
                "ehr_document_id": note.ehr_document_id if note else None,
            }
        )
    return {"tenant": tenant.health_system_name, "encounters": rows}


def _tool_get_note(pipeline, tool_input: dict) -> dict:
    tenant = _require_tenant(pipeline, tool_input["tenant"])
    encounter_id_fragment = tool_input["encounter_id"]
    match = next(
        (
            e
            for e in pipeline.encounter_store.encounters_for_tenant(tenant.id)
            if e.id == encounter_id_fragment or e.id.startswith(encounter_id_fragment)
        ),
        None,
    )
    if match is None:
        raise ValueError(f"No encounter matching '{encounter_id_fragment}' for {tenant.health_system_name}.")
    note = pipeline.get_note(tenant.id, match.id)
    if note is None:
        return {"encounter_id": match.id, "status": match.status.value, "note": None}
    return {
        "encounter_id": match.id,
        "status": match.status.value,
        "generated_by": note.generated_by.value,
        "content_sections": note.content_sections,
        "ehr_document_id": note.ehr_document_id,
    }


def _tool_register_tenant(pipeline, tool_input: dict) -> dict:
    tenant = pipeline.register_tenant(
        tool_input["health_system_name"],
        EHRVendor(tool_input["ehr_vendor"]),
        tool_input["data_residency_region"],
    )
    return {"tenant_id": tenant.id, "health_system_name": tenant.health_system_name}


def _tool_set_template(pipeline, tool_input: dict) -> dict:
    tenant = _require_tenant(pipeline, tool_input["tenant"])
    template = pipeline.set_template(tenant.id, tool_input["specialty"], tool_input["section_schema"])
    return {
        "tenant": tenant.health_system_name,
        "specialty": template.specialty,
        "section_schema": template.section_schema,
    }


def _tool_submit_encounter(pipeline, tool_input: dict) -> dict:
    tenant = _require_tenant(pipeline, tool_input["tenant"])
    encounter = pipeline.submit_encounter(
        tenant.id, tool_input["clinician_id"], tool_input["specialty"], tool_input["audio_text"]
    )
    note = pipeline.get_note(tenant.id, encounter.id)
    return {
        "encounter_id": encounter.id,
        "status": encounter.status.value,
        "content_sections": note.content_sections if note else None,
        "ehr_document_id": note.ehr_document_id if note else None,
    }


# One handler per entry in TOOLS above — keeps each tool's schema and
# implementation easy to find together when adding a new one.
TOOL_HANDLERS = {
    "list_tenants": _tool_list_tenants,
    "get_metrics": _tool_get_metrics,
    "list_encounters": _tool_list_encounters,
    "get_note": _tool_get_note,
    "register_tenant": _tool_register_tenant,
    "set_template": _tool_set_template,
    "submit_encounter": _tool_submit_encounter,
}


def _execute_tool(pipeline, name: str, tool_input: dict) -> dict:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(pipeline, tool_input)
    except Exception as exc:  # tool errors get fed back to the model, not raised
        return {"error": str(exc)}


class PlatformAssistant:
    def __init__(self, api_key: str | None = None, force_mock: bool = False):
        self._client = resolve_client(api_key, force_mock)

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def respond(self, pipeline, conversation: list[dict], user_message: str) -> str:
        """Appends the user turn (and any tool/assistant turns) to `conversation`
        in place and returns the assistant's final reply text."""
        conversation.append({"role": "user", "content": user_message})
        if self._client is None:
            reply = self._respond_mock(pipeline, user_message)
            conversation.append({"role": "assistant", "content": reply})
            return reply
        try:
            return self._respond_live(pipeline, conversation)
        except Exception as exc:
            reply = f"[assistant error, falling back to command mode] {self._respond_mock(pipeline, user_message)}\n\n(live error: {exc})"
            conversation.append({"role": "assistant", "content": reply})
            return reply

    def _respond_live(self, pipeline, conversation: list[dict]) -> str:
        for _ in range(6):  # bound the tool-use loop
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation,
            )
            # Convert SDK content blocks to plain dicts before storing them in
            # `conversation` — session state persists across Streamlit reruns,
            # and round-tripping raw pydantic objects through that boundary is
            # brittle, so keep the conversation history JSON-plain-dict shaped.
            content_blocks = [block.model_dump() for block in response.content]

            if response.stop_reason != "tool_use":
                text = "".join(block.text for block in response.content if block.type == "text")
                conversation.append({"role": "assistant", "content": content_blocks})
                return text or "(no response)"

            conversation.append({"role": "assistant", "content": content_blocks})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _execute_tool(pipeline, block.name, block.input)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
                    )
            conversation.append({"role": "user", "content": tool_results})

        conversation.append({"role": "assistant", "content": "I wasn't able to finish that in a reasonable number of steps — could you narrow the request?"})
        return conversation[-1]["content"]

    @staticmethod
    def _respond_mock(pipeline, user_message: str) -> str:
        """Small keyword-driven command parser used when no live Claude client
        is available, so the chat tab still demos something real offline."""
        text = user_message.strip().lower()

        if "tenant" in text and ("list" in text or "which" in text or "who" in text or text.startswith("tenants")):
            result = _execute_tool(pipeline, "list_tenants", {})
            if not result["tenants"]:
                return "No tenants onboarded yet — register one from the sidebar."
            lines = [f"- {t['health_system_name']} ({t['ehr_vendor']}, {t['data_residency_region']})" for t in result["tenants"]]
            return "[MOCK MODE — set ANTHROPIC_API_KEY for free-form chat] Onboarded tenants:\n" + "\n".join(lines)

        metrics_match = re.search(r"metrics?\s+(?:for\s+|on\s+)?(.+)", text)
        if metrics_match:
            result = _execute_tool(pipeline, "get_metrics", {"tenant": metrics_match.group(1)})
            if "error" in result:
                return f"[MOCK MODE] {result['error']}"
            return (
                f"[MOCK MODE] {result['tenant']}: captured={result['encounters_captured']}, "
                f"delivered={result['encounters_delivered']}, notes={result['notes_generated']}, "
                f"avg ASR latency={result['avg_asr_latency_ms']}ms"
            )

        encounters_match = re.search(r"encounters?\s+(?:for\s+|on\s+)?(.+)", text)
        if encounters_match:
            result = _execute_tool(pipeline, "list_encounters", {"tenant": encounters_match.group(1)})
            if "error" in result:
                return f"[MOCK MODE] {result['error']}"
            if not result["encounters"]:
                return f"[MOCK MODE] No encounters yet for {result['tenant']}."
            lines = [f"- {e['short_id']} ({e['specialty']}, {e['status']})" for e in result["encounters"]]
            return f"[MOCK MODE] Encounters for {result['tenant']}:\n" + "\n".join(lines)

        return (
            "[MOCK MODE — set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN for free-form chat] "
            "I can run a few recognized commands offline: \"list tenants\", \"metrics for <tenant>\", "
            "\"encounters for <tenant>\". For anything else, connect a live Claude API key."
        )
