## Architecture

```text
GitHub repository
|------ ↓ git clone / git pull
Amazon EC2
|------ ├── heartbeat.timer
|------ │       ↓ every minute
|------ │   heartbeat.service
|------ │       ↓
|------ │   heartbeat.py
|------ │       ↓
|------ │   /var/lib/heartbeat/events.jsonl
|------ │
|------ └── heartbeat-web.service
|-------------- ↓ always running
            Gunicorn + Flask
|-------------- ↓
            Reads events.jsonl
|-------------- ↓
            Browser
```

## Repository structure

```text
EC2_Heartbeat_Python_Automation/
├── src/
│   ├── heartbeat.py
│   └── app.py
├── templates/
│   └── index.html
├── tests/
│   └── test_heartbeat.py
├── systemd/
│   ├── heartbeat.service
│   ├── heartbeat.timer
│   └── heartbeat-web.service
├── .gitignore
├── README.md
└── requirements.txt
```

## Security

The application follows several security practices:

- Runs under a dedicated Linux service account
- Does not require root privileges
- Uses systemd service isolation
- Restricts write access to the event storage directory
- Stores runtime configuration through environment variables
- Uses Security Groups to limit network access
- Automatically restarts failed services

## Data Flow

1. systemd timer triggers every minute
2. heartbeat.service executes heartbeat.py
3. heartbeat.py generates a heartbeat record
4. Record is appended to events.jsonl
5. Flask application reads events.jsonl
6. Browser requests data through /api/events
7. Dashboard displays the latest records

## Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.11 |
| Web Framework | Flask |
| WSGI Server | Gunicorn |
| Scheduling | systemd timer |
| Service Management | systemd |
| Hosting | Amazon EC2 |
| Source Control | Git / GitHub |
| Data Format | JSONL |
| Testing | pytest |

## Components

### app.py

`app.py` is the Flask web app that reads the heartbeat events from `events.jsonl` and shows them on a simple dashboard. It exposes a few HTTP endpoints:

- `/` renders the browser dashboard
- `/api/events` returns the same data as JSON
- `/health` returns a status response for quick health checks

This keeps the monitoring page separate from the scheduled job itself.

### heartbeat.py

`heartbeat.py` creates one JSON heartbeat record each time the script runs. It gathers the job name, timestamp, EC2 hostname, environment, OS, Python version, and process ID, then appends that data to the log file.

Example output:

```json
{
  "run_id": "bba3be35-66f3-4cc9-8bc3-3c63662fcb6f",
  "job_name": "guid-heartbeat",
  "status": "success",
  "timestamp_utc": "2026-10-05T22:01:00.128419+00:00",
  "environment": "production",
  "hostname": "ip-172-31-15-80",
  "operating_system": "Linux",
  "python_version": "3.11.9",
  "process_id": 1842
}
```

### index.html

`index.html` is the dashboard page shown in the browser. It reads the event data from the Flask app and displays it in a table, with automatic refresh so the newest heartbeat records appear without reloading the page.


### test_heartbeat.py

The test suite checks that the heartbeat output contains the expected fields and that the generated run ID and timestamp are valid.

### systemd service and timer notes

#### * heartbeat.service

Important details:

- Type=oneshot means the script runs once and exits after completion
- the service uses a dedicated Linux account instead of root
- ReadWritePaths restricts where the automation can write files
- output is sent to the Linux journal
- environment variables control configuration and runtime behavior

The checked-in service runs as the dedicated `heartbeat` account and uses the paths shown in the deployment instructions below.

#### * heartbeat.timer

`Persistent=true` ensures the job is triggered again if the server was offline when the timer was scheduled to fire.

#### * heartbeat-web.service

This service starts the Flask dashboard with Gunicorn so the web page stays available in the background. It uses the same `events.jsonl` file as the heartbeat job and restarts automatically if the app stops unexpectedly.

### requirements.txt

This file lists the Python packages needed by the project. The core script uses the standard library, while the dashboard adds Flask and Gunicorn.

### .gitignore

This file keeps generated log data and environment-specific files out of source control.

## Future Architecture Enhancements

Current State:
EC2 → JSONL File → Flask → Browser

Potential Improvements:

- SQLite for structured storage
- PostgreSQL for persistence
- Nginx reverse proxy
- HTTPS with Let's Encrypt
- CloudWatch logging
- Docker containerization
- CI/CD with GitHub Actions
- AWS Load Balancer