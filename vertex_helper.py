import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from emergency_content import SYSTEM_PROMPT, RED_FLAG_HINTS, DEMO_PROFILE

PROJECT_ID = "daniel-reyes-uprm"
LOCATION = "global"
MODEL_NAME = "gemini-2.5-flash"


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
        http_options=types.HttpOptions(api_version="v1"),
    )


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    raise ValueError("Model did not return valid JSON")


def _contextual_fallback(user_text: str, current_case: Optional[str]) -> Dict[str, Any]:
    text = (user_text or "").lower().strip()

    if current_case == "severe_bleeding":
        return {
            "reply": "**Apply firm direct pressure on the wound and call 911 now.**\n- Press hard with a clean cloth or gauze — do not lift it to check.\n- Add more material on top if blood soaks through.\n- Do not remove the first layer; it helps clot form.\n- Is the bleeding soaking through the cloth or spurting out?",
            "case_id": "severe_bleeding",
            "call_now": True,
            "escalate_now": True,
            "why": "Active severe bleeding remains the main concern.",
            "current_instruction": "Apply firm direct pressure continuously. Add more cloth or gauze if blood soaks through, but do not remove the first layer.",
            "next_question": "Is the bleeding soaking through or spurting?",
            "handoff_summary": "Possible severe external bleeding. Direct pressure in progress.",
            "step_index": 1,
        }

    if current_case == "stroke":
        return {
            "reply": "**Call 911 immediately and note the exact time symptoms started.**\n- Keep the person seated upright or on their side if drowsy.\n- Do not give food, drink, or any oral medication.\n- Stroke treatment is time-critical — every minute matters.\n- What time did symptoms start, or when were they last normal?",
            "case_id": "stroke",
            "call_now": True,
            "escalate_now": True,
            "why": "Stroke-like symptoms remain the main concern.",
            "current_instruction": "Keep the person seated or safely on their side, monitor breathing, and do not give food, drink, or oral medicine.",
            "next_question": "What time did the symptoms start or when were they last normal?",
            "handoff_summary": "Possible stroke with important onset timing needed.",
            "step_index": 1,
        }

    if current_case == "chest_pain":
        return {
            "reply": "**Have the person stop all activity and rest — call 911 now.**\n- Loosen tight clothing and keep them calm and still.\n- Do not let them drive themselves or walk around.\n- Monitor breathing and responsiveness closely.\n- Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "case_id": "chest_pain",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac emergency remains the main concern.",
            "current_instruction": "Keep the person resting in a comfortable position, loosen tight clothing, and monitor responsiveness and breathing.",
            "next_question": "Is there shortness of breath, sweating, nausea, or spreading pain?",
            "handoff_summary": "Possible heart attack or high-risk chest pain.",
            "step_index": 1,
        }

    if current_case == "choking":
        return {
            "reply": "**Act immediately — give 5 firm back blows between the shoulder blades.**\n- If the object doesn't clear, give 5 abdominal thrusts (Heimlich).\n- Call 911 if the person cannot speak, breathe, or cough at all.\n- Do not do blind finger sweeps in the mouth.\n- Can the person cough or make any sound right now?",
            "case_id": "choking",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible airway blockage remains the main concern.",
            "current_instruction": "Give 5 back blows, then 5 abdominal thrusts if the person cannot breathe or speak.",
            "next_question": "Can the person cough or speak at all?",
            "handoff_summary": "Possible choking with airway obstruction.",
            "step_index": 1,
        }

    if current_case == "not_breathing":
        return {
            "reply": "**Call 911 now and start hands-only CPR immediately.**\n- Place the person flat on their back on a firm surface.\n- Push hard and fast in the center of the chest — 100–120 times per minute.\n- Do not stop until help arrives or they start breathing normally.\n- Is the person breathing normally right now, or only gasping?",
            "case_id": "not_breathing",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac or breathing arrest remains the main concern.",
            "current_instruction": "Start hands-only CPR with hard, fast chest compressions in the center of the chest.",
            "next_question": "Is the person breathing normally or only gasping?",
            "handoff_summary": "Unconscious or not breathing normally. CPR may be needed.",
            "step_index": 1,
        }

    if any(x in text for x in ["not breathing", "gasping", "unconscious", "collapsed"]):
        return {
            "reply": "**Call 911 and start CPR now — do not wait.**\n- Place the person flat on a firm surface.\n- Push hard and fast in the center of the chest, 100–120 times per minute.\n- Keep going until responders arrive or the person starts breathing.\n- Is the person breathing normally, or only gasping?",
            "case_id": "not_breathing",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac or breathing arrest.",
            "current_instruction": "Place the person on their back on a firm surface and begin hands-only CPR if they are not breathing normally.",
            "next_question": "Is the person breathing normally or only gasping?",
            "handoff_summary": "Possible cardiac or breathing arrest.",
            "step_index": 0,
        }

    if any(x in text for x in ["choking", "can't breathe", "cannot breathe", "can't speak"]):
        return {
            "reply": "**Give 5 firm back blows between the shoulder blades right now.**\n- If that fails, give 5 abdominal thrusts (Heimlich maneuver).\n- Call 911 if the person cannot breathe, speak, or cough.\n- Do not do blind finger sweeps.\n- Can the person cough or make any sound at all?",
            "case_id": "choking",
            "call_now": True,
            "escalate_now": True,
            "why": "Airway blockage suspected.",
            "current_instruction": "Give 5 firm back blows between the shoulder blades. If needed, follow with 5 abdominal thrusts.",
            "next_question": "Can the person cough or speak at all?",
            "handoff_summary": "Possible choking with airway obstruction.",
            "step_index": 0,
        }

    if any(x in text for x in ["bleeding", "blood everywhere", "severe bleeding", "won't stop bleeding"]):
        return {
            "reply": "**Press a clean cloth firmly on the wound and hold it — call 911.**\n- Do not lift the cloth to check; keep constant pressure.\n- Add more cloth on top if blood soaks through.\n- Severe bleeding can become fatal in minutes.\n- Is the blood soaking through the cloth, or is it spurting out?",
            "case_id": "severe_bleeding",
            "call_now": True,
            "escalate_now": True,
            "why": "Heavy bleeding can become fatal quickly.",
            "current_instruction": "Press firmly on the wound with clean cloth, gauze, or dressing and keep continuous pressure.",
            "next_question": "Is the bleeding soaking through the cloth or spurting?",
            "handoff_summary": "Possible severe external bleeding.",
            "step_index": 0,
        }

    if any(x in text for x in ["slurred", "face droop", "weak on one side", "stroke"]):
        return {
            "reply": "**Call 911 now and note the exact time symptoms started.**\n- Keep the person seated upright or on their side if drowsy.\n- Do not give food, drink, or any oral medication.\n- Stroke treatment is time-critical — every minute of delay matters.\n- What time did symptoms start, or when were they last acting normally?",
            "case_id": "stroke",
            "call_now": True,
            "escalate_now": True,
            "why": "FAST stroke warning signs reported.",
            "current_instruction": "Keep the person seated upright or safely on their side if drowsy, and do not give food, drink, or oral medication.",
            "next_question": "What time did the symptoms start or when were they last normal?",
            "handoff_summary": "Possible stroke with FAST symptoms.",
            "step_index": 0,
        }

    if any(x in text for x in ["chest pain", "heart attack", "pressure in chest", "tight chest"]):
        return {
            "reply": "**Stop all activity — have the person sit or lie down and call 911.**\n- Loosen any tight clothing and keep them calm.\n- Do not let them walk around or drive themselves.\n- Chest pain with sweating, nausea, or arm/jaw pain is a cardiac emergency.\n- Is there shortness of breath, sweating, nausea, or spreading pain?",
            "case_id": "chest_pain",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac emergency.",
            "current_instruction": "Stop activity, keep the person resting in a comfortable position, and monitor breathing and responsiveness.",
            "next_question": "Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "handoff_summary": "Possible heart attack or high-risk chest pain.",
            "step_index": 0,
        }

    return {
        "reply": "**Tell me the biggest immediate danger so I can help you.**\n- Is the person breathing? Unconscious? Bleeding heavily?\n- Any chest pain, choking, or stroke-like symptoms (slurred speech, face droop, one-sided weakness)?\n- What is the most urgent thing happening right now?",
        "case_id": current_case or "other",
        "call_now": False,
        "escalate_now": False,
        "why": "Not enough detail yet.",
        "current_instruction": "Stay with the person, keep them safe, and tell me the biggest danger first.",
        "next_question": "What is the biggest immediate danger right now?",
        "handoff_summary": "Emergency type not yet clear.",
        "step_index": 0,
    }


def transcribe_audio(audio_bytes: bytes, audio_mime: str) -> str:
    """Transcribe audio using Gemini. Returns transcript text, or empty string on failure."""
    if not audio_bytes:
        return ""
    # Strip codec params — Gemini only accepts the base MIME type (e.g. audio/webm not audio/webm;codecs=opus)
    mime = (audio_mime or "audio/wav").split(";")[0].strip()
    try:
        response = _client().models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text="Transcribe this audio exactly as spoken. "
                                 "Return only the spoken words, nothing else."
                        ),
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=300,
            ),
        )
        return (response.text or "").strip()
    except Exception:
        return ""


def triage_turn(
    user_text: str,
    history: List[Dict[str, str]],
    profile: Optional[Dict[str, Any]] = None,
    image_bytes: Optional[bytes] = None,
    image_mime: Optional[str] = None,
    current_case: Optional[str] = None,
    current_instruction: Optional[str] = None,
    symptom_start_time: Optional[str] = None,
) -> Dict[str, Any]:
    profile = profile or DEMO_PROFILE

    system_instruction = f"""{SYSTEM_PROMPT}

{RED_FLAG_HINTS}

Current active case: {current_case or "unknown"}
Current active instruction: {current_instruction or "none yet"}
Symptom start time: {symptom_start_time or "unknown"}

Medical profile:
{json.dumps(profile, indent=2)}"""

    # Build conversation history as proper Content turns (exclude the latest user message
    # which was just appended to history before this call — we'll add it with media below).
    past_messages = history[:-1][-11:]
    history_contents: List[Any] = []
    for m in past_messages:
        role = "user" if m["role"] == "user" else "model"
        history_contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
        )

    # Current user turn: text + optional image
    current_parts: List[Any] = [types.Part.from_text(text=user_text)]
    if image_bytes and image_mime:
        current_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))

    contents = history_contents + [types.Content(role="user", parts=current_parts)]

    try:
        response = _client().models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=2048,
            ),
        )
        data = _extract_json(response.text)

        case_id = data.get("case_id", "other")
        if current_case and case_id == "other":
            case_id = current_case

        return {
            "reply": data.get("reply", ""),
            "case_id": case_id,
            "call_now": bool(data.get("call_now", False)),
            "escalate_now": bool(data.get("escalate_now", False)),
            "why": data.get("why", ""),
            "current_instruction": data.get("current_instruction", ""),
            "next_question": data.get("next_question", ""),
            "handoff_summary": data.get("handoff_summary", ""),
            "step_index": int(data.get("step_index", 0)),
        }
    except Exception as exc:
        import streamlit as st
        st.error(f"[ResQ AI error — using fallback] {exc}")
        return _contextual_fallback(user_text, current_case)