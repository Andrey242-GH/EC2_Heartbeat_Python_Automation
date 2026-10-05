#!/usr/bin/env python3

import json
import logging
import os
import platform
import socket
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


JOB_NAME = os.getenv("JOB_NAME", "guid-heartbeat")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
OUTPUT_FILE = Path(
    os.getenv(
        "OUTPUT_FILE",
        "/var/lib/heartbeat/events.jsonl"
    )
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("heartbeat")


def create_heartbeat() -> dict:
    """Create one automation heartbeat event."""

    return {
        "run_id": str(uuid.uuid4()),
        "job_name": JOB_NAME,
        "status": "success",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "environment": ENVIRONMENT,
        "hostname": socket.gethostname(),
        "operating_system": platform.system(),
        "python_version": platform.python_version(),
        "process_id": os.getpid(),
    }


def save_heartbeat(event: dict) -> None:
    """Append the event as a JSON line."""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        mode="a",
        encoding="utf-8"
    ) as output:
        output.write(json.dumps(event) + "\n")


def main() -> int:
    try:
        event = create_heartbeat()
        save_heartbeat(event)

        logger.info(
            "Heartbeat created successfully: %s",
            json.dumps(event)
        )

        return 0

    except Exception:
        logger.exception("Heartbeat execution failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())