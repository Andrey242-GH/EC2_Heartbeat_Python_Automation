# Roadmap

This roadmap lists possible improvements; it is not a committed schedule. The project currently creates heartbeat events in JSONL, displays them with a Flask dashboard, and uses systemd to run the job on EC2.

## Near term

- Expand automated tests to cover writing and reading JSONL events, malformed records, and the `/api/events` and `/health` routes.
- Add continuous integration so tests run automatically when changes are pushed or submitted for review.
- Keep local, EC2, and User Data configuration consistent, especially the event-file path and Python dependencies.

## Operations and production readiness

- Add event retention or log rotation so the JSONL file does not grow without a limit.
- Add monitoring and alerts for failed heartbeat runs or heartbeats that stop arriving.
- Serve the dashboard through a reverse proxy with HTTPS instead of exposing the development-facing port directly.
- Document production access controls before making the dashboard available beyond a restricted test network.

## Future options

- Consider SQLite for structured local queries, or PostgreSQL if multiple instances or users need shared storage.
- Add filtering and time-range queries to the dashboard when event volume makes the current recent-events view insufficient.
- Automate repeatable deployments after the manual EC2 and User Data workflows are stable.
