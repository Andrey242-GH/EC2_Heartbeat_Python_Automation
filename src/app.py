import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent

OUTPUT_FILE = Path(
    os.getenv(
        "OUTPUT_FILE",
        PROJECT_DIRECTORY / "events.jsonl",
    )
)

app = Flask(
    __name__,
    template_folder=str(PROJECT_DIRECTORY / "templates"),
)


def read_events(limit: int = 100) -> list[dict]:
    if not OUTPUT_FILE.exists():
        return []

    events = []

    with OUTPUT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    events.reverse()
    return events[:limit]


@app.route("/")
def home():
    events = read_events()

    return render_template(
        "index.html",
        events=events,
        total_events=len(events),
    )


@app.route("/api/events")
def api_events():
    return jsonify(read_events())


@app.route("/health")
def health():
    return jsonify(
        {
            "application": "ec2-heartbeat-automation",
            "status": "healthy",
            "output_file": str(OUTPUT_FILE),
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
    )