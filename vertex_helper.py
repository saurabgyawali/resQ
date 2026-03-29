import json
import re
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from emergency_content import SYSTEM_PROMPT, RED_FLAG_HINTS, DEMO_PROFILE

PROJECT_ID = "daniel-reyes-uprm"
LOCATION = "global"
MODEL_NAME = "gemini-2.5-flash"


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
            return json.loads(match.group(0))
    raise ValueError("Model did not return valid JSON")


def _fallback_triage(user_text: str) -> Dict[str, Any]:
    text = user_text.lower()

    if any(x in text for x in ["not breathing", "gasping", "unconscious", "collapsed"]):
        return {
            "reply": "Call emergency services now. Start CPR if the person is not breathing normally.",
            "case_id": "not_breathing",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac or breathing arrest.",
            "next_question": "Is the person breathing normally right now?",
            "handoff_summary": "Unconscious / not breathing normally. CPR likely needed.",
        }

    if any(x in text for x in ["choking", "can't breathe", "cannot breathe", "can't speak"]):
        return {
            "reply": "This may be choking. Call emergency services now if the person cannot speak or breathe.",
            "case_id": "choking",
            "call_now": True,
            "escalate_now": True,
            "why": "Airway blockage suspected.",
            "next_question": "Can the person speak or cough at all?",
            "handoff_summary": "Possible choking with airway obstruction.",
        }

    if any(x in text for x in ["bleeding", "blood everywhere", "severe bleeding", "won't stop bleeding"]):
        return {
            "reply": "This may be life-threatening bleeding. Apply firm pressure and call emergency services now.",
            "case_id": "severe_bleeding",
            "call_now": True,
            "escalate_now": True,
            "why": "Heavy bleeding can become fatal quickly.",
            "next_question": "Is the bleeding soaking through cloth or clothing?",
            "handoff_summary": "Possible severe external bleeding.",
        }

    if any(x in text for x in ["slurred", "face droop", "weak on one side", "stroke"]):
        return {
            "reply": "This may be a stroke. Call emergency services now and note the time symptoms started.",
            "case_id": "stroke",
            "call_now": True,
            "escalate_now": True,
            "why": "FAST stroke warning signs reported.",
            "next_question": "What time did the symptoms start or when was the person last normal?",
            "handoff_summary": "Possible stroke with FAST symptoms.",
        }

    if any(x in text for x in ["chest pain", "heart attack", "pressure in chest", "tight chest"]):
        return {
            "reply": "This may be a heart attack. Call emergency services now if the pain is severe or persistent.",
            "case_id": "chest_pain",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac emergency.",
            "next_question": "Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "handoff_summary": "Possible heart attack or high-risk chest pain.",
        }

    return {
        "reply": "Tell me the biggest danger first: breathing, bleeding, chest pain, choking, or stroke-like symptoms.",
        "case_id": "other",
        "call_now": False,
        "escalate_now": False,
        "why": "Not enough detail yet.",
        "next_question": "What is happening right now?",
        "handoff_summary": "Emergency type not yet clear.",
    }


def triage_turn(
    user_text: str,
    history: List[Dict[str, str]],
    profile: Optional[Dict[str, Any]] = None,
    image_bytes: Optional[bytes] = None,
    image_mime: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    audio_mime: Optional[str] = None,
) -> Dict[str, Any]:
    profile = profile or DEMO_PROFILE

    transcript = "\n".join(
        [f"{m['role'].upper()}: {m['content']}" for m in history[-6:]]
    )

    prompt = f"""
{SYSTEM_PROMPT}

{RED_FLAG_HINTS}

Medical profile:
{json.dumps(profile, indent=2)}

Conversation so far:
{transcript}

Latest user input:
{user_text}
"""

    contents: List[Any] = [prompt]

    if image_bytes and image_mime:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))

    if audio_bytes and audio_mime:
        contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime))

    try:
        response = _client().models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "max_output_tokens": 400,
            },
        )
        data = _extract_json(response.text)
        return {
            "reply": data.get("reply", ""),
            "case_id": data.get("case_id", "other"),
            "call_now": bool(data.get("call_now", False)),
            "escalate_now": bool(data.get("escalate_now", False)),
            "why": data.get("why", ""),
            "next_question": data.get("next_question", ""),
            "handoff_summary": data.get("handoff_summary", ""),
        }
    except Exception:
        return _fallback_triage(user_text)