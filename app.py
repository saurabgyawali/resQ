import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from db import log_message, log_session
from emergency_content import CASE_GUIDES, DEMO_PROFILE
from modules import (
    apply_styles,
    render_animation,
    render_call_banner,
    render_contacts_card,
    render_handoff_summary,
    render_profile_card,
    render_top_nav,
    scroll_to_top,
)
from vertex_helper import triage_turn, transcribe_audio

st.set_page_config(page_title="ResQ", page_icon="🚑", layout="wide")

PAGES = ["Emergency", "Profile", "Contacts", "Learn"]


def init_state():
    defaults = {
        "page": "Emergency",
        "session_id": str(uuid.uuid4()),
        "session_started_at": datetime.now(timezone.utc).isoformat(),
        "chat_history": [],
        "current_case": None,
        "current_step": 0,
        "escalate_now": False,
        "symptom_start_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "handoff_summary": "",
        "voice_output": True,
        "action_mode": False,
        "current_instruction": "",
        "current_question": "",
        "current_why": "",
        "profile": DEMO_PROFILE,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_page_from_query() -> str:
    raw = st.query_params.get("page", "Emergency")
    for page in PAGES:
        if str(raw).strip().lower() == page.lower():
            return page
    return "Emergency"


def append_message(role: str, content: str, modality: str = "text") -> None:
    st.session_state.chat_history.append({"role": role, "content": content, "modality": modality})

    log_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": st.session_state.session_id,
            "role": role,
            "modality": modality,
            "text": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def run_triage(user_text: str, audio_file=None, image_file=None):
    if not user_text and not audio_file and not image_file:
        st.warning("Describe what is happening, record audio, or add a camera image.")
        return None

    # ── Transcribe audio first (separate call, plain text response) ──
    # This avoids MIME-type issues and JSON-format incompatibility when
    # audio bytes are sent directly to the triage call.
    transcript = ""
    if audio_file:
        with st.spinner("Transcribing audio…"):
            transcript = transcribe_audio(
                audio_file.getvalue(),
                getattr(audio_file, "type", "audio/wav") or "audio/wav",
            )
        if not transcript:
            st.warning("Could not transcribe audio — please add a text description or try again.")
            return None

    # ── Build the effective triage text ──────────────────────────────
    typed = (user_text or "").strip()
    if transcript and typed:
        triage_text = f"{typed} {transcript}"
        user_display = f"{typed} — 🎤 {transcript}"
    elif transcript:
        triage_text = transcript
        user_display = f"🎤 {transcript}"
    else:
        triage_text = typed
        user_display = typed

    # ── Modality tag ─────────────────────────────────────────────────
    modality = "text"
    if audio_file and image_file:
        modality = "multimodal"
    elif audio_file:
        modality = "voice"
    elif image_file:
        modality = "camera"

    append_message("user", user_display, modality=modality)

    # Image is still sent as bytes; audio is now handled via transcript above
    image_bytes = image_file.getvalue() if image_file else None
    image_mime = getattr(image_file, "type", None) if image_file else None

    old_case = st.session_state.get("current_case")

    with st.spinner("Analyzing emergency…"):
        result = triage_turn(
            user_text=triage_text or "Please infer the emergency context from the attached media.",
            history=st.session_state.chat_history,
            profile=st.session_state.profile,
            image_bytes=image_bytes,
            image_mime=image_mime,
            current_case=st.session_state.get("current_case"),
            current_instruction=st.session_state.get("current_instruction", ""),
            symptom_start_time=st.session_state.get("symptom_start_time", ""),
        )

    assistant_reply = result.get("reply", "I need one more short detail to continue safely.")
    append_message("assistant", assistant_reply, modality="ai")

    st.session_state.current_case = result.get("case_id", st.session_state.get("current_case") or "other")
    st.session_state.escalate_now = bool(result.get("escalate_now", False) or result.get("call_now", False))
    st.session_state.handoff_summary = result.get("handoff_summary", "")
    st.session_state.current_instruction = result.get("current_instruction", "")
    st.session_state.current_question = result.get("next_question", "")
    st.session_state.current_why = result.get("why", "")
    st.session_state.action_mode = True

    if old_case != st.session_state.current_case:
        st.session_state.current_step = 0
    else:
        st.session_state.current_step = result.get("step_index", st.session_state.current_step)

    log_session(
        {
            "session_id": st.session_state.session_id,
            "user_id": st.session_state.profile["user_id"],
            "started_at": st.session_state.session_started_at,
            "last_case": st.session_state.current_case,
            "escalated": bool(st.session_state.escalate_now),
            "symptom_start_time": st.session_state.symptom_start_time,
            "location_text": "Demo mode",
            "triage_summary": st.session_state.handoff_summary,
            "status": "active",
        }
    )

    return result


def reset_demo() -> None:
    st.session_state.chat_history = []
    st.session_state.current_case = None
    st.session_state.current_step = 0
    st.session_state.escalate_now = False
    st.session_state.handoff_summary = ""
    st.session_state.action_mode = False
    st.session_state.current_instruction = ""
    st.session_state.current_question = ""
    st.session_state.current_why = ""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.pop("_last_audio_hash", None)
    now = datetime.now(timezone.utc)
    st.session_state.session_started_at = now.isoformat()
    st.session_state.symptom_start_time = now.strftime("%Y-%m-%d %H:%M:%S UTC")


def _ai_avatar():
    """Return the ResQ logo as a PIL Image for chat avatars, fallback to emoji."""
    try:
        from PIL import Image as _PIL
        logo = Path(__file__).parent / "assets" / "animations" / "logo.png"
        if logo.exists():
            return _PIL.open(logo)
    except Exception:
        pass
    return "🚑"


def render_chat_history() -> None:
    if not st.session_state.chat_history:
        return  # empty state — let the container breathe

    avatar = _ai_avatar()
    for msg in st.session_state.chat_history:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(msg["content"])
        else:
            with st.chat_message("user"):
                st.markdown(msg["content"])


QUICK_CASES = [
    ("not_breathing", "💔", "Unconscious",   "The person is unconscious and may not be breathing normally."),
    ("chest_pain",    "🫀", "Chest Pain",    "The person has severe chest pain and may be having a heart attack."),
    ("severe_bleeding","🩸","Bleeding",      "There is heavy bleeding that will not stop."),
    ("choking",       "🫁", "Choking",       "The person is choking and cannot speak or breathe properly."),
    ("stroke",        "🧠", "Stroke Signs",  "The person has slurred speech, face droop, or one-sided weakness."),
]


def render_emergency_page():
    # Handle quick-case pill click (query param driven so active state persists on rerun)
    qc = st.query_params.get("quickcase", "")
    if qc and not st.session_state.action_mode:
        for key, _icon, _label, prompt in QUICK_CASES:
            if key == qc:
                if run_triage(prompt):
                    st.query_params.clear()
                    st.rerun()
                break

    if not st.session_state.action_mode:
        # ── Hero ──────────────────────────────────────────────────
        st.markdown(
            """
            <div class="hero-card center-input">
              <div class="hero-eyebrow">AI-powered first-aid guidance</div>
              <div class="hero-title">What's the emergency?</div>
              <div class="hero-subtitle">
                Tap a common emergency below for instant guidance,
                or describe the situation yourself.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Quick-case pills ──────────────────────────────────────
        pills_html = '<div class="quick-grid">'
        for key, icon, label, _ in QUICK_CASES:
            active_cls = "active" if key == qc else ""
            pills_html += (
                f'<a class="quick-pill {active_cls}" href="?quickcase={key}" target="_self">'
                f'<span class="quick-icon">{icon}</span>'
                f'<span>{label}</span>'
                f'</a>'
            )
        pills_html += "</div>"
        st.markdown(pills_html, unsafe_allow_html=True)

        # ── Divider ───────────────────────────────────────────────
        st.markdown('<div class="or-divider">or describe it yourself</div>', unsafe_allow_html=True)

        # ── Input mode segmented control ──────────────────────────
        input_modes = [
            ("type",   "⌨️", "Type"),
            ("voice",  "🎤", "Voice"),
            ("camera", "📷", "Camera"),
        ]
        mode = st.query_params.get("mode", "type")
        if mode not in ("type", "voice", "camera"):
            mode = "type"

        mode_html = '<div class="mode-selector">'
        for key, icon, label in input_modes:
            active_cls = "active" if key == mode else ""
            mode_html += (
                f'<a class="mode-pill {active_cls}" href="?mode={key}" target="_self">'
                f'{icon} {label}'
                f'</a>'
            )
        mode_html += "</div>"
        st.markdown(mode_html, unsafe_allow_html=True)

        # ── Input widgets ─────────────────────────────────────────
        user_text = ""
        audio_file = None
        image_file = None

        with st.container():
            if mode == "type":
                user_text = st.text_area(
                    "Describe the emergency",
                    placeholder="Example: My dad suddenly has slurred speech and his right arm is weak.",
                    height=120,
                    label_visibility="collapsed",
                )
            elif mode == "voice":
                user_text = st.text_area(
                    "Optional typed context",
                    placeholder="Optional: add any quick context here",
                    height=80,
                    label_visibility="collapsed",
                )
                audio_file = st.audio_input("Record symptoms")
                if audio_file is not None:
                    audio_hash = hash(audio_file.getvalue())
                    if audio_hash != st.session_state.get("_last_audio_hash"):
                        st.session_state._last_audio_hash = audio_hash
                        if run_triage(user_text, audio_file=audio_file):
                            st.rerun()
            else:
                user_text = st.text_area(
                    "Optional typed context",
                    placeholder="Optional: add any quick context here",
                    height=80,
                    label_visibility="collapsed",
                )
                image_file = st.camera_input("Capture image if safe")

        st.write("")
        if st.button("Get emergency guidance →", type="primary", use_container_width=True):
            if run_triage(user_text, audio_file=audio_file, image_file=image_file):
                st.rerun()

    else:
        # Fire scroll immediately so the sticky chat_input footer
        # appearing for the first time doesn't pull the viewport down.
        scroll_to_top()

        case_key = st.session_state.current_case or "other"
        case_data = CASE_GUIDES.get(case_key, CASE_GUIDES["other"])

        if st.session_state.escalate_now:
            render_call_banner(case_data["title"], can_cancel=True)

        follow_up = st.chat_input("Answer the question above or add any new detail")
        if follow_up:
            run_triage(follow_up)
            st.rerun()

        left, right = st.columns([1.2, 0.8], gap="large")

        with left:
            with st.container(height=500, border=False):
                render_chat_history()

        with right:
            if case_data.get("animation"):
                render_animation(case_data["animation"], case_data["title"])

            render_handoff_summary(
                summary=st.session_state.handoff_summary or case_data["summary"],
                profile=DEMO_PROFILE,
                symptom_start=st.session_state.symptom_start_time,
            )

            if st.button("← Back to intake", use_container_width=True):
                st.session_state.action_mode = False
                st.session_state.current_case = None
                st.session_state.current_step = 0
                st.session_state.escalate_now = False
                st.session_state.current_instruction = ""
                st.session_state.current_question = ""
                st.session_state.current_why = ""
                st.session_state.chat_history = []
                st.session_state.pop("_last_audio_hash", None)
                st.rerun()

        # Fire again after all content is in the DOM to catch any late layout shifts
        scroll_to_top()


def render_learn_page():
    st.markdown('<div class="page-title">Learn First Aid</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Step-by-step guides for the five most common emergencies. '
        'Select a topic to read the protocol, then practice with AI.</div>',
        unsafe_allow_html=True,
    )

    LEARN_CASES = [
        ("not_breathing", "💔", "CPR"),
        ("stroke",        "🧠", "Stroke"),
        ("choking",       "🫁", "Choking"),
        ("severe_bleeding","🩸","Bleeding"),
        ("chest_pain",    "🫀", "Chest Pain"),
    ]

    tab_labels = [f"{icon} {label}" for _, icon, label in LEARN_CASES]
    tabs = st.tabs(tab_labels)

    for tab, (key, icon, label) in zip(tabs, LEARN_CASES):
        case = CASE_GUIDES[key]
        with tab:
            left, right = st.columns([1.1, 0.9], gap="large")

            with left:
                # Summary banner
                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-bottom:1rem;">
                      <div class="learn-case-title">{icon} {case['title']}</div>
                      <div class="learn-case-summary">{case['summary']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Steps
                st.markdown('<div class="learn-section-label">What to do — step by step</div>', unsafe_allow_html=True)
                for i, step in enumerate(case["steps"], 1):
                    st.markdown(
                        f"""
                        <div class="learn-step">
                          <div class="learn-step-num">{i}</div>
                          <div class="learn-step-text">{step}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Do-not warnings
                if case.get("do_not"):
                    st.markdown('<div class="learn-section-label" style="margin-top:1rem;">What NOT to do</div>', unsafe_allow_html=True)
                    warnings_html = "".join(
                        f'<div class="learn-warning-item">⚠ {w}</div>'
                        for w in case["do_not"]
                    )
                    st.markdown(f'<div class="warning-box">{warnings_html}</div>', unsafe_allow_html=True)

            with right:
                if case.get("animation"):
                    render_animation(case["animation"], case["title"])

                # Practice CTA
                practice_prompt = {
                    "not_breathing":  "The person is unconscious and may not be breathing normally.",
                    "stroke":         "The person has slurred speech, face droop, or one-sided weakness.",
                    "choking":        "The person is choking and cannot speak or breathe properly.",
                    "severe_bleeding":"There is heavy bleeding that will not stop.",
                    "chest_pain":     "The person has severe chest pain and may be having a heart attack.",
                }.get(key, "")

                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-top:1rem;text-align:center;">
                      <div class="learn-section-label" style="margin-bottom:0.5rem;">Ready to practice?</div>
                      <div style="color:var(--text-muted);font-size:0.9rem;margin-bottom:0.9rem;">
                        Run a live AI simulation for <strong>{case['title']}</strong>.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Practice {label} →", key=f"practice_{key}", use_container_width=True, type="primary"):
                    reset_demo()
                    if run_triage(practice_prompt):
                        st.query_params["page"] = "Emergency"
                        st.rerun()


def main():
    init_state()
    st.session_state.page = current_page_from_query()

    # Handle 911 cancel before any rendering
    if st.query_params.get("cancel_911") == "1":
        st.session_state.escalate_now = False
        del st.query_params["cancel_911"]

    apply_styles()
    render_top_nav(st.session_state.page)

    if st.session_state.page == "Emergency":
        render_emergency_page()
    elif st.session_state.page == "Profile":
        render_profile_card(DEMO_PROFILE)
    elif st.session_state.page == "Contacts":
        render_contacts_card(DEMO_PROFILE)
    elif st.session_state.page == "Learn":
        render_learn_page()


if __name__ == "__main__":
    main()