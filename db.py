from functools import lru_cache
from typing import Dict, List, Optional

from google.cloud import bigquery

PROJECT_ID = "daniel-reyes-uprm"
DATASET = "resqHack"


@lru_cache(maxsize=1)
def get_client() -> Optional[bigquery.Client]:
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception:
        return None


def _insert(table_name: str, rows: List[Dict]) -> None:
    client = get_client()
    if not client:
        return
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    try:
        client.insert_rows_json(table_id, rows)
    except Exception:
        pass


def log_session(session_row: Dict) -> None:
    _insert("EmergencySessions", [session_row])


def log_message(message_row: Dict) -> None:
    _insert("EmergencyMessages", [message_row])


def seed_animation_metadata() -> None:
    rows = [
        {"case_id": "not_breathing", "title": "CPR", "local_path": "assets/animations/cpr.gif", "mime_type": "image/gif", "offline_ready": True},
        {"case_id": "choking", "title": "Choking", "local_path": "assets/animations/choking.gif", "mime_type": "image/gif", "offline_ready": True},
        {"case_id": "severe_bleeding", "title": "Bleeding", "local_path": "assets/animations/bleeding.gif", "mime_type": "image/gif", "offline_ready": True},
        {"case_id": "stroke", "title": "Stroke", "local_path": "assets/animations/stroke.gif", "mime_type": "image/gif", "offline_ready": True},
        {"case_id": "chest_pain", "title": "Chest Pain", "local_path": "assets/animations/chest_pain.gif", "mime_type": "image/gif", "offline_ready": True},
    ]
    _insert("AnimationAssets", rows)