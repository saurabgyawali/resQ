import base64
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

    logo_path = Path(__file__).parent / "assets" / "animations" / "logo.png"
    logo_html = ""
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:36px;width:auto;display:block;" alt="ResQ logo">'

    def pill(label: str) -> str:
        active = "active" if label == selected_page else ""
        href = f"?page={quote_plus(label)}"
        return f'<a class="nav-pill {active}" href="{href}" target="_self">{label}</a>'

    links = "".join([pill(p) for p in pages])

    st.markdown(
        f"""
        <div class="top-nav-wrap">
          <div class="top-nav">
            <a href="?page=Emergency" target="_self" style="text-decoration:none;display:flex;align-items:center;gap:0.5rem;">
              {logo_html}
              <div class="top-nav-brand">ResQ</div>
            </a>
            <div class="top-nav-links">{links}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def scroll_to_top() -> None:
    components.html(
        """<script>
           (function() {
             function up() {
               try {
                 var selectors = [
                   '[data-testid="stAppViewContainer"]',
                   '[data-testid="stMain"]',
                   '.main'
                 ];
                 selectors.forEach(function(sel) {
                   var el = window.parent.document.querySelector(sel);
                   if (el) { el.scrollTop = 0; }
                 });
                 window.parent.document.documentElement.scrollTop = 0;
                 window.parent.document.body.scrollTop = 0;
                 window.parent.scrollTo({top: 0, behavior: 'instant'});
               } catch(e) {}
             }
             up();
             [100, 300, 600, 1000, 1500, 2200].forEach(function(ms) {
               setTimeout(up, ms);
             });
           })();
        </script>""",
        height=0,
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
    circ = round(2 * 3.14159 * 40, 1)
    components.html(
        f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:'Inter','Segoe UI',Arial,sans-serif;background:transparent;}}
  .banner{{
    background:linear-gradient(135deg,#D64045 0%,#B83039 100%);
    border-radius:22px;padding:1.1rem 1.25rem 1.3rem;color:#fff;
    box-shadow:0 14px 32px rgba(214,64,69,.30);
  }}
  .badge{{
    display:inline-block;padding:.28rem .7rem;border-radius:999px;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.24);
    font-weight:800;font-size:.75rem;letter-spacing:.05em;margin-bottom:.45rem;
  }}
  .case-title{{font-size:.95rem;font-weight:700;opacity:.88;margin-bottom:.9rem;}}
  .body-row{{display:flex;align-items:center;gap:1.25rem;}}
  .ring-wrap{{position:relative;width:96px;height:96px;flex-shrink:0;}}
  .ring-wrap svg{{transform:rotate(-90deg);}}
  .ring-bg{{fill:none;stroke:rgba(255,255,255,.20);stroke-width:7;}}
  .ring-fg{{
    fill:none;stroke:#fff;stroke-width:7;stroke-linecap:round;
    stroke-dasharray:{circ};stroke-dashoffset:0;
    transition:stroke-dashoffset .85s linear,stroke .3s;
  }}
  .num{{
    position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
    font-size:2.3rem;font-weight:900;color:#fff;
  }}
  .right{{flex:1;}}
  .lbl{{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.65;margin-bottom:.2rem;}}
  .big{{font-size:1.55rem;font-weight:900;line-height:1.15;margin-bottom:.85rem;}}
  .btn-row{{display:flex;gap:.6rem;flex-wrap:wrap;}}
  .btn-cancel{{
    padding:.6rem 1.1rem;border-radius:12px;
    border:2px solid rgba(255,255,255,.38);background:rgba(255,255,255,.10);
    color:#fff;font-weight:800;font-size:.88rem;cursor:pointer;
    font-family:inherit;transition:background .18s;
  }}
  .btn-cancel:hover{{background:rgba(255,255,255,.22);}}
  .btn-call{{
    padding:.6rem 1.1rem;border-radius:12px;border:none;
    background:#fff;color:#D64045;font-weight:900;font-size:.88rem;
    cursor:pointer;font-family:inherit;transition:opacity .18s,transform .18s;
    text-decoration:none;display:inline-flex;align-items:center;gap:.4rem;
  }}
  .btn-call:hover{{opacity:.9;transform:translateY(-1px);}}
  @keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.18)}}}}
  .tick{{animation:pulse .25s ease;}}
  /* Cancelled state */
  #cancelled-view{{display:none;}}
  #active-view{{display:block;}}
</style>
</head><body>

<!-- Active countdown view -->
<div class="banner" id="active-view">
  <div class="badge">🚨 Emergency escalation recommended</div>
  <div class="case-title">{case_title}</div>
  <div class="body-row">
    <div class="ring-wrap">
      <svg width="96" height="96" viewBox="0 0 100 100">
        <circle class="ring-bg" cx="50" cy="50" r="40"/>
        <circle class="ring-fg" cx="50" cy="50" r="40" id="ring"/>
      </svg>
      <div class="num" id="num">10</div>
    </div>
    <div class="right">
      <div class="lbl" id="lbl">Calling 911 in</div>
      <div class="big" id="big">10 seconds</div>
      <div class="btn-row">
        {'<button class="btn-cancel" onclick="cancelCall()">✕&nbsp; Cancel</button>' if can_cancel else ''}
        <a class="btn-call" id="call-btn" href="tel:911" onclick="onCallClick(event)">📞&nbsp; Call 911 Now</a>
      </div>
    </div>
  </div>
</div>

<!-- Cancelled view (shown instantly on cancel, no page reload yet) -->
<div class="banner" id="cancelled-view">
  <div class="badge">Escalation paused</div>
  <div class="big" style="margin-bottom:.75rem;">Call cancelled.</div>
  <div style="opacity:.82;font-size:.93rem;margin-bottom:1rem;">
    Changed your mind? You can still call 911 right now.
  </div>
  <div class="btn-row">
    <a class="btn-call" href="tel:911" onclick="onCallClick(event)">📞&nbsp; Call 911</a>
  </div>
</div>

<script>
  var CIRC={circ}, TOTAL=10, n=TOTAL, done=false;
  var ring=document.getElementById('ring');
  var numEl=document.getElementById('num');
  var bigEl=document.getElementById('big');
  var lblEl=document.getElementById('lbl');

  function updateRing(){{
    ring.style.strokeDashoffset=((TOTAL-n)/TOTAL)*CIRC;
    ring.style.stroke=(n<=3)?'#FFD03A':'#fff';
  }}
  function tick(){{
    numEl.classList.remove('tick');
    void numEl.offsetWidth;
    numEl.classList.add('tick');
    numEl.textContent=n;
    bigEl.textContent=n===1?'1 second':n+' seconds';
    updateRing();
  }}

  var iv=setInterval(function(){{
    if(done)return;
    n--; tick();
    if(n<=0){{clearInterval(iv);triggerCall();}}
  }},1000);

  function triggerCall(){{
    done=true; clearInterval(iv);
    lblEl.textContent='Opening phone app…';
    bigEl.textContent='';
    numEl.textContent='📞';
    // Small delay so user sees the "Opening…" text before the browser switches
    setTimeout(function(){{
      window.parent.location.href='tel:911';
    }},300);
  }}

  function onCallClick(e){{
    // Let the native <a href="tel:911"> handle it — no JS override needed.
    // Just clean up the countdown so it doesn't auto-call again.
    done=true; clearInterval(iv);
  }}

  function cancelCall(){{
    done=true; clearInterval(iv);
    // Instantly swap to cancelled view — no page reload
    document.getElementById('active-view').style.display='none';
    document.getElementById('cancelled-view').style.display='block';
    // After 2 s, quietly tell Python that escalation is cancelled
    setTimeout(function(){{
      var url=new URL(window.parent.location.href);
      url.searchParams.set('cancel_911','1');
      window.parent.location.replace(url.toString());
    }},2000);
  }}
</script>
</body></html>""",
        height=260,
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
    name = contact["name"]
    relationship = contact["relationship"]
    phone = contact["phone"]
    first_name = name.split()[0]
    initials = "".join(w[0].upper() for w in name.split()[:2])

    st.markdown('<div class="page-title">Emergency Contacts</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Reach the right people instantly when it counts.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        # ── Contact card + call button ─────────────────────────
        st.markdown(
            f"""
            <div class="contact-card">
              <div class="contact-avatar">{initials}</div>
              <div class="contact-name">{name}</div>
              <div class="contact-rel-badge">{relationship}</div>
              <div class="contact-phone">{phone}</div>
            </div>
            <a class="contact-call-btn" href="tel:{phone}">📞&nbsp; Call {first_name}</a>
            """,
            unsafe_allow_html=True,
        )

        # ── What to say script ─────────────────────────────────
        st.markdown(
            """
            <div class="glass-card" style="margin-top:1rem;">
              <div class="instruction-title" style="margin-bottom:0.75rem;">What to say</div>
              <div class="say-item">📍&nbsp; Share your exact location first</div>
              <div class="say-item">🚨&nbsp; Describe the emergency briefly and clearly</div>
              <div class="say-item">👤&nbsp; Name the person who needs help</div>
              <div class="say-item">📋&nbsp; Mention any known conditions or medications</div>
              <div class="say-item last">✅&nbsp; Stay on the line until help arrives</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        # ── Quick-dial emergency numbers ───────────────────────
        st.markdown(
            """
            <div class="glass-card" style="margin-bottom:1rem;">
              <div class="instruction-title" style="margin-bottom:0.875rem;">Quick Dial</div>

              <div class="emg-row">
                <div>
                  <div class="emg-label">Emergency Services</div>
                  <div class="emg-desc">Police · Fire · Ambulance</div>
                </div>
                <a class="emg-call emg-911" href="tel:911">📞 911</a>
              </div>

              <div class="emg-row">
                <div>
                  <div class="emg-label">Poison Control</div>
                  <div class="emg-desc">Ingestion or exposure</div>
                </div>
                <a class="emg-call" href="tel:18002221222">800-222-1222</a>
              </div>

              <div class="emg-row">
                <div>
                  <div class="emg-label">Crisis Helpline</div>
                  <div class="emg-desc">Mental health emergencies</div>
                </div>
                <a class="emg-call" href="tel:988">📞 988</a>
              </div>

              <div class="emg-row last">
                <div>
                  <div class="emg-label">Non-Emergency Line</div>
                  <div class="emg-desc">Local police, non-urgent</div>
                </div>
                <a class="emg-call" href="tel:311">📞 311</a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Before you call tip ────────────────────────────────
        st.markdown(
            """
            <div class="glass-card">
              <div class="instruction-title" style="margin-bottom:0.5rem;">Before you call</div>
              <p style="font-size:0.9rem;line-height:1.7;color:var(--t2);margin:0;">
                Stay calm and speak clearly. Have the patient's name, age, location, and
                current symptoms ready. If calling 911, stay on the line — dispatchers can
                guide you through first-aid steps until help arrives.
              </p>
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