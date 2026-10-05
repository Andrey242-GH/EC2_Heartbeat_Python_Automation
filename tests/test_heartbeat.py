import sys
import uuid
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from heartbeat import create_heartbeat


def test_create_heartbeat():
    event = create_heartbeat()

    assert event["status"] == "success"
    assert event["job_name"]
    assert event["timestamp_utc"]
    assert event["hostname"]

    uuid.UUID(event["run_id"])
    datetime.fromisoformat(event["timestamp_utc"])