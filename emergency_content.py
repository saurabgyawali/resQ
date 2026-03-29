DEMO_USER_ID = "demo-user-1"

DEMO_PROFILE = {
    "user_id": DEMO_USER_ID,
    "full_name": "Maria Rivera",
    "age": 67,
    "blood_type": "O+",
    "conditions": ["Type 2 diabetes", "Hypertension"],
    "allergies": ["Penicillin"],
    "medications": ["Metformin", "Lisinopril"],
    "emergency_contact": {
        "name": "Daniel Rivera",
        "relationship": "Son",
        "phone": "+1-787-555-0199",
    },
}

CASE_GUIDES = {
    "not_breathing": {
        "title": "Unconscious / Not Breathing Normally",
        "animation": "assets/animations/cpr.gif",
        "summary": "Start CPR and get emergency help immediately.",
        "steps": [
            "Call 911 now and send someone to get an AED if one is nearby.",
            "Place the person flat on their back on a firm surface.",
            "Start hands-only CPR: place both hands in the center of the chest.",
            "Push hard and fast at 100 to 120 compressions per minute.",
            "Use the AED as soon as it arrives and follow its prompts.",
        ],
        "do_not": [
            "Do not delay CPR to keep checking for signs over and over.",
            "Do not stop compressions unless the person clearly starts breathing, an AED tells you to pause, or responders take over.",
        ],
    },
    "choking": {
        "title": "Choking",
        "animation": "assets/animations/choking.gif",
        "summary": "If the person cannot speak or breathe, act immediately.",
        "steps": [
            "Call 911 if the person cannot speak, cough, or breathe.",
            "Stand to the side and slightly behind the person.",
            "Give 5 firm back blows between the shoulder blades.",
            "If needed, give 5 abdominal thrusts.",
            "Repeat 5 back blows and 5 abdominal thrusts until the object comes out or the person becomes unresponsive.",
        ],
        "do_not": [
            "Do not give food or water.",
            "Do not put your fingers in the mouth unless you can clearly see the object.",
        ],
    },
    "severe_bleeding": {
        "title": "Severe Bleeding",
        "animation": "assets/animations/bleeding.gif",
        "summary": "Control bleeding fast while emergency help is on the way.",
        "steps": [
            "Call 911 for heavy or life-threatening bleeding.",
            "Apply firm direct pressure with a clean cloth, dressing, or gauze.",
            "If blood soaks through, add more material and keep pressing.",
            "If trained and the bleeding is life-threatening from an arm or leg, apply a tourniquet above the wound.",
            "Keep the person still and warm until responders arrive.",
        ],
        "do_not": [
            "Do not keep lifting the cloth to check the wound.",
            "Do not remove a tourniquet once placed.",
        ],
    },
    "stroke": {
        "title": "Possible Stroke",
        "animation": "assets/animations/stroke.gif",
        "summary": "Use FAST signs and treat it as an emergency.",
        "steps": [
            "Call 911 now.",
            "Note the exact time the symptoms started or were last known normal.",
            "Keep the person seated upright or on their side if drowsy or vomiting.",
            "Stay calm and keep monitoring breathing and responsiveness.",
            "Be ready to tell responders the start time and the person’s known conditions.",
        ],
        "do_not": [
            "Do not give food, drink, or oral medication.",
            "Do not let the person go to sleep without monitoring them.",
        ],
    },
    "chest_pain": {
        "title": "Chest Pain / Possible Heart Attack",
        "animation": "assets/animations/chest_pain.gif",
        "summary": "Persistent or severe chest pain should be treated as an emergency.",
        "steps": [
            "Call 911 now if the pain is severe, crushing, spreading, or comes with shortness of breath, sweating, or nausea.",
            "Help the person stop activity and sit or rest in a comfortable position.",
            "Loosen tight clothing and keep them calm.",
            "If they have prescribed heart medicine, help them use it as directed.",
            "If they collapse and stop breathing normally, start CPR.",
        ],
        "do_not": [
            "Do not have the person drive themselves.",
            "Do not ignore chest pain that lasts more than a few minutes.",
        ],
    },
    "other": {
        "title": "Other Emergency",
        "animation": "",
        "summary": "Keep the person safe and escalate if symptoms are serious.",
        "steps": [
            "If the person is getting worse, call 911 now.",
            "Keep them safe, still, and monitored.",
            "Answer the next questions so ResQ can narrow the emergency type.",
        ],
        "do_not": [
            "Do not give food, drink, or medication unless you are sure it is safe.",
        ],
    },
}

SYSTEM_PROMPT = """
You are ResQ, a hackathon emergency triage assistant for non-medical bystanders.
Your job:
1) Ask one short follow-up question at a time when needed.
2) Route only into one of these cases:
   - not_breathing
   - choking
   - severe_bleeding
   - stroke
   - chest_pain
   - other
3) If there is any red flag, set call_now=true and escalate_now=true.
4) Keep reply under 30 words.
5) Never claim a definitive diagnosis.
6) Use the provided medical profile if relevant.
7) Return valid JSON only.

Required JSON keys:
reply
case_id
call_now
escalate_now
why
next_question
handoff_summary
"""

RED_FLAG_HINTS = """
Escalate immediately if the person:
- is unconscious
- is not breathing normally or is gasping
- has severe chest pain
- has one-sided weakness, face droop, or slurred speech
- has heavy bleeding
- cannot speak or breathe because of choking
"""