import uuid
from datetime import datetime, timezone

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
)
from vertex_helper import triage_turn

st.set_page_config(page_title="ResQ", page_icon="🚑", layout="wide")

PAGES = ["Emergency", "Profile", "Contacts", "Learn"]


def init_state():
    defaults = {
        "page": "Emergency",
        "session_id": str(uuid.uuid4()),
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
    st.session_state.chat_history.append({"role": role, "content": content})

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

    user_display = user_text.strip() if user_text else "[voice/camera input]"
    modality = "text"
    if audio_file and image_file:
        modality = "multimodal"
    elif audio_file:
        modality = "voice"
    elif image_file:
        modality = "camera"

    append_message("user", user_display, modality=modality)

    image_bytes = image_file.getvalue() if image_file else None
    image_mime = getattr(image_file, "type", None) if image_file else None
    audio_bytes = audio_file.getvalue() if audio_file else None
    audio_mime = getattr(audio_file, "type", None) if audio_file else None

    old_case = st.session_state.get("current_case")

    result = triage_turn(
        user_text=user_text or "Please infer the emergency context from the attached media.",
        history=st.session_state.chat_history,
        profile=DEMO_PROFILE,
        image_bytes=image_bytes,
        image_mime=image_mime,
        audio_bytes=audio_bytes,
        audio_mime=audio_mime,
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

    log_session(
        {
            "session_id": st.session_state.session_id,
            "user_id": DEMO_PROFILE["user_id"],
            "started_at": datetime.now(timezone.utc).isoformat(),
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
    st.session_state.symptom_start_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def render_chat_history() -> None:
    if not st.session_state.chat_history:
        st.info("ResQ will ask short follow-up questions here.")
        return

    for msg in st.session_state.chat_history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.write(msg["content"])


def render_emergency_page():
    st.markdown('<div class="page-title">ResQ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Emergency help for ordinary people before professional help arrives.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.action_mode:
        st.markdown(
            """
            <div class="hero-card center-input">
              <div class="hero-title">What is happening?</div>
              <div class="hero-subtitle">
                Describe the emergency, record a voice note, or use the camera if it is safe.
                ResQ will route you into guided action mode.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        mode = st.radio(
            "Input mode",
            ["Type", "Voice", "Camera"],
            horizontal=True,
            label_visibility="collapsed",
        )

        user_text = ""
        audio_file = None
        image_file = None

        with st.container():
            if mode == "Type":
                user_text = st.text_area(
                    "Describe the emergency",
                    placeholder="Example: My dad suddenly has slurred speech and his right arm is weak.",
                    height=120,
                    label_visibility="collapsed",
                )
            elif mode == "Voice":
                user_text = st.text_area(
                    "Optional typed context",
                    placeholder="Optional: add any quick context here",
                    height=100,
                    label_visibility="collapsed",
                )
                audio_file = st.audio_input("Record symptoms")
            else:
                user_text = st.text_area(
                    "Optional typed context",
                    placeholder="Optional: add any quick context here",
                    height=100,
                    label_visibility="collapsed",
                )
                image_file = st.camera_input("Capture image if safe")

        st.write("")
        quick_cols = st.columns(5)
        quick_cases = [
            ("Person is unconscious", "The person is unconscious and may not be breathing normally."),
            ("Chest pain", "The person has severe chest pain and may be having a heart attack."),
            ("Heavy bleeding", "There is heavy bleeding that will not stop."),
            ("Choking", "The person is choking and cannot speak or breathe properly."),
            ("Stroke symptoms", "The person has slurred speech, face droop, or one-sided weakness."),
        ]

        for col, (label, prompt) in zip(quick_cols, quick_cases):
            with col:
                if st.button(label, use_container_width=True):
                    run_triage(prompt)
                    st.rerun()

        if st.button("Start emergency guidance", type="primary", use_container_width=True):
            run_triage(user_text, audio_file=audio_file, image_file=image_file)
            st.rerun()

    else:
        case_key = st.session_state.current_case or "other"
        case_data = CASE_GUIDES.get(case_key, CASE_GUIDES["other"])

        if st.session_state.escalate_now:
            render_call_banner(case_data["title"], can_cancel=True)

        follow_up = st.chat_input("Answer the last question or add a new detail")
        if follow_up:
            run_triage(follow_up)
            st.rerun()

        left, right = st.columns([1.15, 0.85], gap="large")

        with left:
            st.markdown("### Live guidance")
            render_chat_history()

        with right:
            if case_data.get("animation"):
                render_animation(case_data["animation"], case_data["title"])

            st.markdown("### Current guidance")
            current_instruction = (
                st.session_state.get("current_instruction")
                or case_data["steps"][st.session_state.current_step]
            )

            st.markdown(
                f"""
                <div class="instruction-box">
                  <div class="instruction-title">Do this now</div>
                  <div>{current_instruction}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("current_why"):
                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-top:0.75rem;">
                      <strong>Why this matters</strong><br>
                      {st.session_state.current_why}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if st.session_state.get("current_question"):
                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-top:0.75rem;">
                      <strong>Next question</strong><br>
                      {st.session_state.current_question}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("### Protocol steps")
            for idx, step in enumerate(case_data["steps"]):
                label = "Current step" if idx == st.session_state.current_step else f"Step {idx + 1}"
                st.markdown(
                    f"""
                    <div class="instruction-box">
                      <div class="instruction-title">{label}</div>
                      <div>{step}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            render_handoff_summary(
                summary=st.session_state.handoff_summary or case_data["summary"],
                profile=DEMO_PROFILE,
                symptom_start=st.session_state.symptom_start_time,
            )

            action_cols = st.columns(2)
            with action_cols[0]:
                if st.button("Back to intake", use_container_width=True):
                    st.session_state.action_mode = False
                    st.session_state.current_case = None
                    st.session_state.current_step = 0
                    st.session_state.escalate_now = False
                    st.session_state.current_instruction = ""
                    st.session_state.current_question = ""
                    st.session_state.current_why = ""
                    st.rerun()

            with action_cols[1]:
                if st.button("Reset demo", use_container_width=True):
                    reset_demo()
                    st.rerun()


def render_learn_page():
    st.markdown('<div class="page-title">Learn / Practice</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Judge-friendly demo page for the five MVP emergency guides.</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    cases = ["not_breathing", "stroke", "choking", "severe_bleeding", "chest_pain"]

    for idx, key in enumerate(cases):
        case = CASE_GUIDES[key]
        with cols[idx % 2]:
            st.markdown(
                f"<div class='glass-card'><h3>{case['title']}</h3><p>{case['summary']}</p></div>",
                unsafe_allow_html=True,
            )
            if case["animation"]:
                render_animation(case["animation"], case["title"])


def main():
    init_state()
    st.session_state.page = current_page_from_query()

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