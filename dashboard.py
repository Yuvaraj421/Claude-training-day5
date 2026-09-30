"""Commure Clinical Documentation Automation — Streamlit dashboard.

A platform-operator's view of the multi-tenant pipeline described in
claude_in_healthcare/05-commure-clinical-documentation-automation.md: register
health-system tenants on different EHR vendors, configure per-specialty note
templates, submit encounters, and watch per-tenant throughput.

Uses `orchestrator.MultiTenantPipeline` directly (not the REST API in
main.py) so the whole demo runs in a single `streamlit run dashboard.py` with
no server to stand up separately.

Educational demo only — not a real clinical system. All tenants, clinicians,
and transcripts here are synthetic.

Run:
    streamlit run dashboard.py
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from assistant import PlatformAssistant
from models import EHRVendor, EncounterStatus
from orchestrator import MultiTenantPipeline
from sample_data import create_sample_encounters, seed_sample_tenants

# -- Palette (validated categorical theme, fixed order — see dataviz skill) ----
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
ACCENT = CATEGORICAL[0]
ACCENT_DARK = "#1f5aa0"
STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"
CARD = "#ffffff"
GRIDLINE = "#e1e0d9"
BORDER = "rgba(11,11,11,0.10)"

STATUS_ICONS = {
    EncounterStatus.CAPTURING: "🎙️",
    EncounterStatus.TRANSCRIBING: "📝",
    EncounterStatus.DRAFTING: "🧠",
    EncounterStatus.DELIVERED: "✅",
}
STAGE_LABELS = {
    EncounterStatus.CAPTURING: "Capturing",
    EncounterStatus.TRANSCRIBING: "Transcribing (ASR)",
    EncounterStatus.DRAFTING: "Drafting (LLM)",
    EncounterStatus.DELIVERED: "Delivered to EHR",
}
STAGE_ORDER = [
    EncounterStatus.CAPTURING,
    EncounterStatus.TRANSCRIBING,
    EncounterStatus.DRAFTING,
    EncounterStatus.DELIVERED,
]

st.set_page_config(page_title="Commure Clinical Documentation Automation", layout="wide", page_icon="🏥")

# -- Global look & feel ---------------------------------------------------------
st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 1.6rem; }}

    /* Hero header */
    .cds-hero {{
        display:flex; align-items:center; justify-content:space-between; gap:16px;
        padding-bottom:16px; margin-bottom:12px; border-bottom:1px solid {GRIDLINE};
        flex-wrap:wrap;
    }}
    .cds-hero h1 {{ margin:0; font-size:1.7rem; line-height:1.25; }}
    .cds-hero p {{ margin:4px 0 0 0; color:{INK_MUTED}; font-size:0.92rem; max-width:640px; }}
    .cds-pill {{
        display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
        border-radius:999px; padding:6px 14px; font-size:0.83rem; font-weight:600;
        border:1px solid; flex-shrink:0;
    }}

    /* Tabs */
    button[data-baseweb="tab"] {{ font-weight:600; font-size:0.95rem; }}
    div[data-baseweb="tab-highlight"] {{ background-color: {ACCENT} !important; height:3px; }}

    /* Primary buttons */
    .stButton > button[kind="primary"] {{
        background-color:{ACCENT}; border-color:{ACCENT}; border-radius:8px;
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color:{ACCENT_DARK}; border-color:{ACCENT_DARK};
    }}
    .stButton > button {{ border-radius:8px; }}

    /* Bordered containers -> soft cards */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius:12px; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color:{CARD}; border-right:1px solid {GRIDLINE}; }}

    /* Tenant chip */
    .cds-chip {{
        display:flex; align-items:center; gap:8px; padding:8px 10px; margin-bottom:6px;
        border-radius:10px; border:1px solid {GRIDLINE}; background:{SURFACE}; font-size:0.86rem;
    }}
    .cds-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
    .cds-chip-vendor {{
        color:{INK_MUTED}; margin-left:auto; font-size:0.72rem;
        text-transform:uppercase; letter-spacing:.04em;
    }}

    /* Pipeline stepper */
    .cds-stepper {{ display:flex; align-items:flex-start; margin:10px 0 20px 0; }}
    .cds-step {{ flex:1; text-align:center; position:relative; }}
    .cds-step:not(:last-child)::after {{
        content:""; position:absolute; top:14px; left:50%; width:100%; height:2px;
        background:{GRIDLINE}; z-index:0;
    }}
    .cds-step.done:not(:last-child)::after {{ background:{STATUS_GOOD}; }}
    .cds-step-dot {{
        width:28px; height:28px; border-radius:50%; margin:0 auto 8px auto; position:relative; z-index:1;
        display:flex; align-items:center; justify-content:center; font-size:0.85rem; font-weight:700;
        color:white; background:{GRIDLINE}; border:3px solid {SURFACE};
    }}
    .cds-step.done .cds-step-dot {{ background:{STATUS_GOOD}; }}
    .cds-step-label {{ font-size:0.78rem; color:{INK_MUTED}; }}
    .cds-step.done .cds-step-label {{ color:{INK_PRIMARY}; font-weight:600; }}

    /* KPI metric cards */
    div[data-testid="stMetric"] {{ text-align:center; }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "pipeline" not in st.session_state:
    pipeline = MultiTenantPipeline()
    seed_sample_tenants(pipeline)
    st.session_state.pipeline = pipeline
    st.session_state.last_result = None  # (tenant_id, encounter_id)

if "assistant" not in st.session_state:
    st.session_state.assistant = PlatformAssistant()
    st.session_state.chat_conversation = []  # raw anthropic-format messages fed back into the API
    st.session_state.chat_display = []  # [(role, text)] for rendering only

pipeline: MultiTenantPipeline = st.session_state.pipeline
assistant: PlatformAssistant = st.session_state.assistant


def tenant_label(tenant) -> str:
    return f"{tenant.health_system_name} ({tenant.ehr_vendor.value})"


def tenant_color(index: int) -> str:
    return CATEGORICAL[index % len(CATEGORICAL)]


def select_tenant(tenants: list, key: str | None = None):
    """Renders a tenant selectbox keyed by display label and returns the
    chosen Tenant. Shared by any tab that lets the operator pick one tenant
    out of the onboarded list."""
    tenant_options = {tenant_label(t): t for t in tenants}
    chosen_label = st.selectbox("Tenant", list(tenant_options.keys()), key=key)
    return tenant_options[chosen_label]


def render_stepper(reached_index: int) -> None:
    """Renders the capture -> ASR -> LLM -> EHR pipeline as a connected step
    row, with everything up to the reached stage marked complete."""
    steps_html = []
    for i, stage in enumerate(STAGE_ORDER):
        done = i <= reached_index
        icon = "✓" if done else str(i + 1)
        steps_html.append(
            f'<div class="cds-step {"done" if done else ""}">'
            f'<div class="cds-step-dot">{icon}</div>'
            f'<div class="cds-step-label">{STAGE_LABELS[stage]}</div>'
            f"</div>"
        )
    st.markdown(f'<div class="cds-stepper">{"".join(steps_html)}</div>', unsafe_allow_html=True)


tenants = pipeline.tenant_store.list_tenants()
live = pipeline.documentation_agent.llm_client.is_live
badge_color = STATUS_GOOD if live else STATUS_WARNING
badge_text = "● Live — documentation via Claude" if live else "● Mock mode — set ANTHROPIC_API_KEY for live drafting"

# -- Hero header -----------------------------------------------------------------
st.markdown(
    f"""
    <div class="cds-hero">
        <div>
            <h1>🏥 Commure Clinical Documentation Automation</h1>
            <p>Ambient dictation → ASR → LLM-drafted note → EHR delivery, per health-system tenant.
            Educational demo — all tenants and transcripts are synthetic.</p>
        </div>
        <span class="cds-pill" style="background:{badge_color}1a;color:{badge_color};border-color:{badge_color}55;">
            {badge_text}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -- Sidebar: tenant onboarding + roster ------------------------------------------
with st.sidebar:
    st.markdown("#### 🏥 Commure Platform")
    st.caption(
        "Educational demo inspired by the Commure — Clinical Documentation "
        "Automation at Scale case study. Not a disclosure of Commure's real "
        "system; all data is synthetic."
    )

    st.divider()
    st.markdown("**Register a new tenant**")
    with st.form("register_tenant_form", clear_on_submit=True):
        name = st.text_input("Health system name")
        vendor = st.selectbox("EHR vendor", [v.value for v in EHRVendor])
        region = st.text_input("Data residency region", value="us-east")
        if st.form_submit_button("Register tenant", type="primary", use_container_width=True) and name:
            tenant = pipeline.register_tenant(name, EHRVendor(vendor), region)
            st.success(f"Registered **{name}** — tenant `{tenant.id[:8]}`")
            st.rerun()

    st.divider()
    st.markdown(f"**Onboarded tenants** &nbsp;·&nbsp; {len(tenants)}")
    for i, t in enumerate(tenants):
        st.markdown(
            f'<div class="cds-chip">'
            f'<span class="cds-dot" style="background:{tenant_color(i)};"></span>'
            f"{t.health_system_name}"
            f'<span class="cds-chip-vendor">{t.ehr_vendor.value}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    if not tenants:
        st.caption("No tenants yet — register one above.")

tab_submit, tab_templates, tab_monitor, tab_history, tab_assistant = st.tabs(
    ["📝 Submit Encounter", "⚙️ Tenant Templates", "📊 Platform Monitoring", "🗂️ Encounter History", "💬 Assistant"]
)

# -- Tab: Submit Encounter -----------------------------------------------------
with tab_submit:
    if not tenants:
        st.info("Register a tenant in the sidebar to get started.")
    else:
        col_form, col_result = st.columns([1, 1.4], gap="large")

        with col_form:
            with st.container(border=True):
                st.markdown("##### 📝 Submit an encounter")
                tenant = select_tenant(tenants)

                existing_specialties = list(tenant.note_templates.keys())
                specialty_choice = st.selectbox("Specialty", existing_specialties + ["Other (type below)"])
                specialty = (
                    st.text_input("Custom specialty", value="general")
                    if specialty_choice == "Other (type below)"
                    else specialty_choice
                )

                clinician_id = st.text_input("Clinician ID", value="dr-demo")

                samples = {s.label: s for s in create_sample_encounters()}
                sample_choice = st.selectbox("Load a sample dictation (optional)", ["— none —"] + list(samples.keys()))
                default_text = samples[sample_choice].raw_audio_text if sample_choice in samples else ""
                audio_text = st.text_area("Encounter audio (dictated text stand-in)", value=default_text, height=160)

                submit = st.button("🚀 Submit encounter", type="primary", use_container_width=True)

        with col_result:
            with st.container(border=True):
                st.markdown("##### 📈 Pipeline result")
                if submit:
                    if not audio_text.strip():
                        st.warning("Enter or load some dictation text first.")
                    else:
                        with st.spinner("Running capture → ASR → LLM drafting → EHR delivery..."):
                            encounter = pipeline.submit_encounter(tenant.id, clinician_id, specialty, audio_text)
                        st.session_state.last_result = (tenant.id, encounter.id)

                result = st.session_state.last_result
                if result is None:
                    st.caption("Submit an encounter to see the generated note and EHR delivery result here.")
                else:
                    result_tenant_id, encounter_id = result
                    encounter = pipeline.encounter_store.get_encounter(result_tenant_id, encounter_id)
                    note = pipeline.get_note(result_tenant_id, encounter_id)
                    result_tenant = pipeline.tenant_store.require_tenant(result_tenant_id)

                    render_stepper(STAGE_ORDER.index(encounter.status))

                    if note is not None:
                        st.markdown(
                            f"**Generated note** &nbsp;"
                            f"<span style='color:{INK_MUTED};font-size:0.85rem;'>"
                            f"(generated_by={note.generated_by.value})</span>",
                            unsafe_allow_html=True,
                        )
                        for section, text in note.content_sections.items():
                            with st.expander(section.replace("_", " ").title(), expanded=True):
                                st.write(text)

                        st.markdown("**EHR delivery**")
                        st.success(
                            f"Routed to **{result_tenant.ehr_vendor.value}** adapter — "
                            f"document ID `{note.ehr_document_id}`",
                            icon="✅",
                        )

                        with st.expander("Event log for this encounter"):
                            events = [
                                e for e in pipeline.bus.events() if e.payload.get("encounter_id") == encounter_id
                            ]
                            for e in events:
                                st.text(f"[{e.timestamp.isoformat(timespec='milliseconds')}] {e.topic}: {e.payload}")

# -- Tab: Tenant Templates ------------------------------------------------------
with tab_templates:
    if not tenants:
        st.info("Register a tenant in the sidebar to configure templates.")
    else:
        tenant = select_tenant(tenants, key="template_tenant_select")

        col_existing, col_new = st.columns([1.2, 1], gap="large")

        with col_existing:
            with st.container(border=True):
                st.markdown("##### 📋 Existing templates")
                if tenant.note_templates:
                    st.table(
                        [
                            {"Specialty": spec, "Section schema": " → ".join(tmpl.section_schema)}
                            for spec, tmpl in tenant.note_templates.items()
                        ]
                    )
                else:
                    st.caption("No templates configured yet — encounters fall back to a generic SOAP schema.")

        with col_new:
            with st.container(border=True):
                st.markdown("##### ➕ Add / update a template")
                with st.form("template_form"):
                    specialty = st.text_input("Specialty")
                    sections_raw = st.text_input(
                        "Section schema (comma-separated, in order)",
                        value="subjective, objective, assessment, plan",
                    )
                    if st.form_submit_button("Save template", type="primary", use_container_width=True) and specialty:
                        section_schema = [s.strip() for s in sections_raw.split(",") if s.strip()]
                        pipeline.set_template(tenant.id, specialty, section_schema)
                        st.success(f"Saved template for **{specialty}**")
                        st.rerun()

# -- Tab: Platform Monitoring ---------------------------------------------------
with tab_monitor:
    if not tenants:
        st.info("Register a tenant and submit an encounter to see platform metrics.")
    else:
        metrics_by_tenant = {t.id: pipeline.get_metrics(t.id) for t in tenants}

        total_captured = sum(m.encounters_captured for m in metrics_by_tenant.values())
        total_delivered = sum(m.encounters_delivered for m in metrics_by_tenant.values())
        total_notes = sum(m.notes_generated for m in metrics_by_tenant.values())
        latencies = [m.avg_asr_latency_ms for m in metrics_by_tenant.values() if m.transcripts_completed]
        platform_avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

        st.markdown("##### 📊 Platform throughput")
        kpi_cols = st.columns(4)
        kpi_specs = [
            ("👥 Tenants onboarded", len(tenants)),
            ("🎙️ Encounters captured", total_captured),
            ("📝 Notes generated", total_notes),
            ("⏱️ Avg ASR latency (ms)", platform_avg_latency),
        ]
        for col, (label, value) in zip(kpi_cols, kpi_specs):
            with col:
                with st.container(border=True):
                    st.metric(label, value)

        st.markdown("##### 📈 Per-tenant comparison")
        names = [t.health_system_name for t in tenants]
        colors = [tenant_color(i) for i in range(len(tenants))]

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1, st.container(border=True):
            delivered = [metrics_by_tenant[t.id].encounters_delivered for t in tenants]
            fig = go.Figure(
                go.Bar(
                    x=names,
                    y=delivered,
                    marker_color=colors,
                    text=delivered,
                    textposition="outside",
                    hovertemplate="%{x}<br>Encounters delivered: %{y}<extra></extra>",
                )
            )
            fig.update_layout(
                title="Encounters delivered by tenant",
                plot_bgcolor=CARD,
                paper_bgcolor=CARD,
                font_color=INK_PRIMARY,
                yaxis=dict(gridcolor=GRIDLINE, zerolinecolor=GRIDLINE),
                xaxis=dict(showgrid=False),
                bargap=0.35,
                showlegend=False,
                margin=dict(t=48, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2, st.container(border=True):
            latency = [metrics_by_tenant[t.id].avg_asr_latency_ms for t in tenants]
            fig = go.Figure(
                go.Bar(
                    x=names,
                    y=latency,
                    marker_color=colors,
                    text=[f"{v:.0f}" for v in latency],
                    textposition="outside",
                    hovertemplate="%{x}<br>Avg ASR latency: %{y} ms<extra></extra>",
                )
            )
            fig.update_layout(
                title="Avg ASR latency by tenant (ms)",
                plot_bgcolor=CARD,
                paper_bgcolor=CARD,
                font_color=INK_PRIMARY,
                yaxis=dict(gridcolor=GRIDLINE, zerolinecolor=GRIDLINE),
                xaxis=dict(showgrid=False),
                bargap=0.35,
                showlegend=False,
                margin=dict(t=48, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw per-tenant metrics table"):
            st.table(
                [
                    {
                        "Tenant": t.health_system_name,
                        "EHR vendor": t.ehr_vendor.value,
                        "Region": t.data_residency_region,
                        "Captured": metrics_by_tenant[t.id].encounters_captured,
                        "Transcribed": metrics_by_tenant[t.id].transcripts_completed,
                        "Notes generated": metrics_by_tenant[t.id].notes_generated,
                        "Delivered": metrics_by_tenant[t.id].encounters_delivered,
                        "Avg ASR latency (ms)": metrics_by_tenant[t.id].avg_asr_latency_ms,
                    }
                    for t in tenants
                ]
            )

# -- Tab: Encounter History -----------------------------------------------------
with tab_history:
    if not tenants:
        st.info("Register a tenant and submit an encounter to see encounter history.")
    else:
        rows = []
        for t in tenants:
            for encounter in pipeline.encounter_store.encounters_for_tenant(t.id):
                note = pipeline.get_note(t.id, encounter.id)
                rows.append(
                    {
                        "Tenant": t.health_system_name,
                        "Encounter ID": encounter.id[:8],
                        "Clinician": encounter.clinician_id,
                        "Specialty": encounter.specialty,
                        "Status": f"{STATUS_ICONS.get(encounter.status, '')} {encounter.status.value.title()}",
                        "EHR vendor": t.ehr_vendor.value,
                        "EHR document ID": note.ehr_document_id if note else "—",
                    }
                )
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No encounters submitted yet.")

# -- Tab: Assistant --------------------------------------------------------------
with tab_assistant:
    st.markdown("##### 💬 Platform operations assistant")
    if assistant.is_live:
        st.caption(
            "Ask about tenants, metrics, encounters, or ask it to onboard a tenant, "
            "update a template, or submit an encounter — it calls the same pipeline as the other tabs."
        )
    else:
        st.caption(
            "Mock mode — set ANTHROPIC_API_KEY for free-form chat. Try commands like "
            "\"list tenants\", \"metrics for Riverside\", or \"encounters for Lakeshore\"."
        )

    if not st.session_state.chat_display:
        with st.chat_message("assistant"):
            st.markdown(
                "👋 Hi! I can look up tenants, metrics, and encounters, or submit a new encounter for you. "
                "Try a quick action below, or ask your own question."
            )

    suggestions = ["List all tenants"]
    if tenants:
        suggestions.append(f"Show metrics for {tenants[0].health_system_name}")
        suggestions.append("Which tenants are on Epic?")
    quick_action = None
    quick_cols = st.columns(len(suggestions))
    for col, suggestion in zip(quick_cols, suggestions):
        if col.button(suggestion, use_container_width=True, key=f"quick_{suggestion}"):
            quick_action = suggestion

    for role, text in st.session_state.chat_display:
        with st.chat_message(role):
            st.markdown(text)

    typed_message = st.chat_input("Ask about tenants, metrics, or submit an encounter...")
    user_message = quick_action or typed_message
    if user_message:
        st.session_state.chat_display.append(("user", user_message))
        with st.spinner("Thinking..."):
            reply = assistant.respond(pipeline, st.session_state.chat_conversation, user_message)
        st.session_state.chat_display.append(("assistant", reply))
        st.rerun()
