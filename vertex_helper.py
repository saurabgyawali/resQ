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


def _contextual_fallback(user_text: str, current_case: Optional[str]) -> Dict[str, Any]:
    text = (user_text or "").lower().strip()

    if current_case == "severe_bleeding":
        return {
            "reply": "Keep firm direct pressure on the wound right now. Heavy bleeding can become dangerous very quickly, so call emergency services if you have not already. Is the bleeding soaking through the cloth or spurting out?",
            "case_id": "severe_bleeding",
            "call_now": True,
            "escalate_now": True,
            "why": "Active severe bleeding remains the main concern.",
            "current_instruction": "Apply firm direct pressure continuously. Add more cloth or gauze if blood soaks through, but do not remove the first layer.",
            "next_question": "Is the bleeding soaking through or spurting?",
            "handoff_summary": "Possible severe external bleeding. Direct pressure in progress.",
        }

    if current_case == "stroke":
        return {
            "reply": "Call emergency services now and note the exact time symptoms started. Stroke treatment depends heavily on timing. What time was the person last known normal?",
            "case_id": "stroke",
            "call_now": True,
            "escalate_now": True,
            "why": "Stroke-like symptoms remain the main concern.",
            "current_instruction": "Keep the person seated or safely on their side, monitor breathing, and do not give food, drink, or oral medicine.",
            "next_question": "What time did the symptoms start or when were they last normal?",
            "handoff_summary": "Possible stroke with important onset timing needed.",
        }

    if current_case == "chest_pain":
        return {
            "reply": "Have the person stop activity and rest now. Severe or persistent chest pain can be a heart attack, so call emergency services immediately. Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "case_id": "chest_pain",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac emergency remains the main concern.",
            "current_instruction": "Keep the person resting in a comfortable position, loosen tight clothing, and monitor responsiveness and breathing.",
            "next_question": "Is there shortness of breath, sweating, nausea, or spreading pain?",
            "handoff_summary": "Possible heart attack or high-risk chest pain.",
        }

    if current_case == "choking":
        return {
            "reply": "If the person cannot speak or breathe, act now and call emergency services. Choking can become life-threatening within minutes. Can the person cough or speak at all?",
            "case_id": "choking",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible airway blockage remains the main concern.",
            "current_instruction": "Give 5 back blows, then 5 abdominal thrusts if the person cannot breathe or speak.",
            "next_question": "Can the person cough or speak at all?",
            "handoff_summary": "Possible choking with airway obstruction.",
        }

    if current_case == "not_breathing":
        return {
            "reply": "Call emergency services now and start CPR if the person is not breathing normally. Every minute matters in cardiac or breathing arrest. Is the person breathing normally right now or only gasping?",
            "case_id": "not_breathing",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac or breathing arrest remains the main concern.",
            "current_instruction": "Start hands-only CPR with hard, fast chest compressions in the center of the chest.",
            "next_question": "Is the person breathing normally or only gasping?",
            "handoff_summary": "Unconscious or not breathing normally. CPR may be needed.",
        }

    if any(x in text for x in ["not breathing", "gasping", "unconscious", "collapsed"]):
        return {
            "reply": "Call emergency services now and start CPR if the person is not breathing normally. This could be a cardiac or breathing emergency. Is the person breathing normally right now or only gasping?",
            "case_id": "not_breathing",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac or breathing arrest.",
            "current_instruction": "Place the person on their back on a firm surface and begin hands-only CPR if they are not breathing normally.",
            "next_question": "Is the person breathing normally or only gasping?",
            "handoff_summary": "Possible cardiac or breathing arrest.",
        }

    if any(x in text for x in ["choking", "can't breathe", "cannot breathe", "can't speak"]):
        return {
            "reply": "This may be choking, so act immediately and call emergency services if the person cannot speak or breathe. Airway blockage can become critical very quickly. Can the person cough or speak at all?",
            "case_id": "choking",
            "call_now": True,
            "escalate_now": True,
            "why": "Airway blockage suspected.",
            "current_instruction": "Give 5 firm back blows between the shoulder blades. If needed, follow with 5 abdominal thrusts.",
            "next_question": "Can the person cough or speak at all?",
            "handoff_summary": "Possible choking with airway obstruction.",
        }

    if any(x in text for x in ["bleeding", "blood everywhere", "severe bleeding", "won't stop bleeding"]):
        return {
            "reply": "Apply firm direct pressure to the wound right now and call emergency services if the bleeding is heavy. Severe bleeding can become life-threatening quickly. Is the bleeding soaking through the cloth or spurting out?",
            "case_id": "severe_bleeding",
            "call_now": True,
            "escalate_now": True,
            "why": "Heavy bleeding can become fatal quickly.",
            "current_instruction": "Press firmly on the wound with clean cloth, gauze, or dressing and keep continuous pressure.",
            "next_question": "Is the bleeding soaking through the cloth or spurting?",
            "handoff_summary": "Possible severe external bleeding.",
        }

    if any(x in text for x in ["slurred", "face droop", "weak on one side", "stroke"]):
        return {
            "reply": "This may be a stroke, so call emergency services now and note the time the symptoms started. Stroke treatment depends heavily on timing. What time did the symptoms start or when was the person last normal?",
            "case_id": "stroke",
            "call_now": True,
            "escalate_now": True,
            "why": "FAST stroke warning signs reported.",
            "current_instruction": "Keep the person seated upright or safely on their side if drowsy, and do not give food, drink, or oral medication.",
            "next_question": "What time did the symptoms start or when were they last normal?",
            "handoff_summary": "Possible stroke with FAST symptoms.",
        }

    if any(x in text for x in ["chest pain", "heart attack", "pressure in chest", "tight chest"]):
        return {
            "reply": "This may be a heart attack, so have the person rest and call emergency services now if the pain is severe or persistent. Chest pain with shortness of breath, sweating, or nausea is especially concerning. Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "case_id": "chest_pain",
            "call_now": True,
            "escalate_now": True,
            "why": "Possible cardiac emergency.",
            "current_instruction": "Stop activity, keep the person resting in a comfortable position, and monitor breathing and responsiveness.",
            "next_question": "Is there shortness of breath, sweating, nausea, or pain spreading to the arm or jaw?",
            "handoff_summary": "Possible heart attack or high-risk chest pain.",
        }

    return {
        "reply": "Tell me the biggest danger first: breathing, bleeding, chest pain, choking, or stroke-like symptoms.",
        "case_id": current_case or "other",
        "call_now": False,
        "escalate_now": False,
        "why": "Not enough detail yet.",
        "current_instruction": "Stay with the person, keep them safe, and tell me the biggest danger first.",
        "next_question": "What is the biggest immediate danger right now?",
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
    current_case: Optional[str] = None,
    current_instruction: Optional[str] = None,
    symptom_start_time: Optional[str] = None,
) -> Dict[str, Any]:
    profile = profile or DEMO_PROFILE

    transcript = "\n".join(
        [f"{m['role'].upper()}: {m['content']}" for m in history[-12:]]
    )

    prompt = f"""
{SYSTEM_PROMPT}

{RED_FLAG_HINTS}

Current active case: {current_case or "unknown"}
Current active instruction: {current_instruction or "none yet"}
Symptom start time: {symptom_start_time or "unknown"}

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
                "max_output_tokens": 500,
            },
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
        }
    except Exception:
        return _contextual_fallback(user_text, current_case)