import json
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st
import streamlit.components.v1 as components


def apply_styles() -> None:
    css_path = Path(__file__).parent / "styles.css"
    if not css_path.exists():
        st.warning(f"Missing styles.css at {css_path}")
        return
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_top_nav(selected_page: str = "Emergency") -> None:
    pages = ["Emergency", "Profile", "Contacts", "Learn"]

    def pill(label: str) -> str:
        active = "active" if label == selected_page else ""
        href = f"?page={quote_plus(label)}"
        return f'<a class="nav-pill {active}" href="{href}" target="_self">{label}</a>'

    links = "".join([pill(p) for p in pages])

    st.markdown(
        f"""
        <div class="top-nav-wrap">
          <div class="top-nav">
            <div class="top-nav-brand">ResQ</div>
            <div class="top-nav-links">{links}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def speak_text(text: str, key: str = "speak") -> None:
    if not text:
        return
    safe_text = json.dumps(text)
    components.html(
        f"""
        <script>
          const txt = {safe_text};
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(txt);
          u.rate = 1.0;
          u.pitch = 1.0;
          window.speechSynthesis.speak(u);
        </script>
        """,
        height=0,
    )


def render_call_banner(case_title: str, can_cancel: bool = True) -> None:
    cancel_html = "<div class='emergency-badge'>Tap Cancel if this was accidental</div>" if can_cancel else ""
    st.markdown(
        f"""
        <div class="call-banner">
          <div class="call-row">
            <div>
              <div class="emergency-badge">Emergency escalation recommended</div>
              <h3 style="margin:0.6rem 0 0.3rem 0;">Call 911 now</h3>
              <div>{case_title}</div>
            </div>
            <div style="text-align:right;">
              <a class="nav-pill active" href="tel:911">Call 911</a>
              <div style="margin-top:0.6rem;">{cancel_html}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_case_card(case_data: dict, step_index: int) -> None:
    st.markdown(
        f"""
        <div class="action-card">
          <div class="step-chip">{case_data['title']}</div>
          <div class="instruction-box">
            <div class="instruction-title">Step {step_index + 1}</div>
            <div>{case_data['steps'][step_index]}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if case_data.get("do_not"):
        warnings = "".join([f"<li>{w}</li>" for w in case_data["do_not"]])
        st.markdown(
            f"""
            <div class="warning-box">
              <strong>What not to do</strong>
              <ul>{warnings}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_animation(asset_path: str, caption: str) -> None:
    path = Path(asset_path)
    if path.exists():
        st.image(str(path), use_container_width=True, caption=caption)
    else:
        st.info(f"Add local animation file here: {asset_path}")


def render_profile_card(profile: dict) -> None:
    conditions = "".join([f"<span class='tag-chip'>{x}</span>" for x in profile.get("conditions", [])])
    allergies = "".join([f"<span class='tag-chip'>{x}</span>" for x in profile.get("allergies", [])])
    medications = "".join([f"<span class='tag-chip'>{x}</span>" for x in profile.get("medications", [])])

    st.markdown(
        f"""
        <div class="profile-card">
          <div class="page-title">Medical Profile</div>
          <div class="page-subtitle">Static for hackathon demo</div>
          <div><strong>Name:</strong> {profile['full_name']}</div>
          <div><strong>Age:</strong> {profile['age']}</div>
          <div><strong>Blood type:</strong> {profile['blood_type']}</div>
          <div style="margin-top:0.8rem;"><strong>Known conditions</strong><br>{conditions}</div>
          <div style="margin-top:0.8rem;"><strong>Allergies</strong><br>{allergies}</div>
          <div style="margin-top:0.8rem;"><strong>Medications</strong><br>{medications}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contacts_card(profile: dict) -> None:
    contact = profile["emergency_contact"]
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="page-title">Emergency Contact</div>
          <div><strong>Name:</strong> {contact['name']}</div>
          <div><strong>Relationship:</strong> {contact['relationship']}</div>
          <div><strong>Phone:</strong> {contact['phone']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_handoff_summary(summary: str, profile: dict, symptom_start: str) -> None:
    contact = profile["emergency_contact"]
    st.markdown(
        f"""
        <div class="summary-card">
          <div class="instruction-title">Responder handoff summary</div>
          <div><strong>Likely emergency:</strong> {summary}</div>
          <div><strong>Symptom start time:</strong> {symptom_start}</div>
          <div><strong>Conditions:</strong> {", ".join(profile.get("conditions", []))}</div>
          <div><strong>Allergies:</strong> {", ".join(profile.get("allergies", []))}</div>
          <div><strong>Medications:</strong> {", ".join(profile.get("medications", []))}</div>
          <div><strong>Emergency contact:</strong> {contact['name']} ({contact['phone']})</div>
        </div>
        """,
        unsafe_allow_html=True,
    )