import uuid
from datetime import datetime, timezone

import streamlit as st

from db import log_message, log_session
from emergency_content import CASE_GUIDES, DEMO_PROFILE
from modules import (
    apply_styles,
    render_animation,
    render_call_banner,
    render_case_card,
    render_contacts_card,
    render_handoff_summary,
    render_profile_card,
    render_top_nav,
    speak_text,
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_page_from_query() -> str:
    raw = st.query_params.get("page", "Emergency")
    for page in PAGES:
        if raw.lower() == page.lower():
            return page
    return "Emergency"


def append_message(role: str, content: str):
    st.session_state.chat_history.append({"role": role, "content": content})
    log_message(
        {
            "message_id": str(uuid.uuid4()),
            "session_id": st.session_state.session_id,
            "role": role,
            "modality": "text",
            "text": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def run_triage(user_text: str, audio_file=None, image_file=None):
    if not user_text and not audio_file and not image_file:
        st.warning("Describe what is happening, record audio, or add a camera image.")
        return

    append_message("user", user_text or "[voice/camera input]")

    image_bytes = image_file.getvalue() if image_file else None
    image_mime = getattr(image_file, "type", None) if image_file else None
    audio_bytes = audio_file.getvalue() if audio_file else None
    audio_mime = getattr(audio_file, "type", None) if audio_file else None

    result = triage_turn(
        user_text=user_text or "Use the attached media to understand the emergency.",
        history=st.session_state.chat_history,
        profile=DEMO_PROFILE,
        image_bytes=image_bytes,
        image_mime=image_mime,
        audio_bytes=audio_bytes,
        audio_mime=audio_mime,
    )

    append_message("assistant", result["reply"])

    st.session_state.current_case = result["case_id"]
    st.session_state.escalate_now = result["escalate_now"] or result["call_now"]
    st.session_state.handoff_summary = result["handoff_summary"]
    st.session_state.current_step = 0
    st.session_state.action_mode = True

    log_session(
        {
            "session_id": st.session_state.session_id,
            "user_id": DEMO_PROFILE["user_id"],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_case": result["case_id"],
            "escalated": bool(st.session_state.escalate_now),
            "symptom_start_time": st.session_state.symptom_start_time,
            "location_text": "Demo mode",
            "triage_summary": result["handoff_summary"],
            "status": "active",
        }
    )


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
                This prototype always keeps emergency escalation visible.
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

        st.markdown('<div class="center-input">', unsafe_allow_html=True)
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

        quick_cols = st.columns(5)
        quick_cases = [
            "Person is unconscious",
            "Chest pain",
            "Heavy bleeding",
            "Choking",
            "Stroke symptoms",
        ]
        for col, label in zip(quick_cols, quick_cases):
            with col:
                if st.button(label, use_container_width=True):
                    run_triage(label)

        if st.button("Start emergency guidance", type="primary", use_container_width=True):
            run_triage(user_text, audio_file=audio_file, image_file=image_file)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        case_key = st.session_state.current_case or "other"
        case_data = CASE_GUIDES.get(case_key, CASE_GUIDES["other"])

        if st.session_state.escalate_now:
            render_call_banner(case_data["title"], can_cancel=True)

        left, right = st.columns([1.15, 0.85], gap="large")

        with left:
            st.markdown('<div class="action-card">', unsafe_allow_html=True)
            st.markdown("### Live guidance")
            for msg in st.session_state.chat_history[-6:]:
                speaker = "You" if msg["role"] == "user" else "ResQ"
                st.markdown(f"**{speaker}:** {msg['content']}")
            st.markdown("</div>", unsafe_allow_html=True)

            follow_up = st.chat_input("Answer the last question or add new details")
            if follow_up:
                run_triage(follow_up)

        with right:
            if case_data.get("animation"):
                render_animation(case_data["animation"], case_data["title"])

            render_case_card(case_data, st.session_state.current_step)

            step_cols = st.columns(3)
            with step_cols[0]:
                if st.button("Previous step", use_container_width=True, disabled=st.session_state.current_step == 0):
                    st.session_state.current_step -= 1
                    st.rerun()
            with step_cols[1]:
                if st.button("Read aloud", use_container_width=True):
                    speak_text(case_data["steps"][st.session_state.current_step])
            with step_cols[2]:
                if st.button(
                    "Next step",
                    use_container_width=True,
                    disabled=st.session_state.current_step >= len(case_data["steps"]) - 1,
                ):
                    st.session_state.current_step += 1
                    st.rerun()

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
                    st.rerun()
            with action_cols[1]:
                if st.button("Reset demo", use_container_width=True):
                    for key in ["chat_history", "current_case", "current_step", "handoff_summary"]:
                        st.session_state[key] = [] if key == "chat_history" else 0 if key == "current_step" else None
                    st.session_state.action_mode = False
                    st.session_state.escalate_now = False
                    st.session_state.session_id = str(uuid.uuid4())
                    st.rerun()


def render_learn_page():
    st.markdown('<div class="page-title">Learn / Practice</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Judge-friendly demo page for the five MVP emergency guides.</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for idx, key in enumerate(["not_breathing", "stroke", "choking", "severe_bleeding", "chest_pain"]):
        with cols[idx % 2]:
            case = CASE_GUIDES[key]
            st.markdown(f"<div class='glass-card'><h3>{case['title']}</h3><p>{case['summary']}</p></div>", unsafe_allow_html=True)
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