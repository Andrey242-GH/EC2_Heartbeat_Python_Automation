# EC2 Heartbeat Automation

This project creates a lightweight heartbeat for EC2-based automation jobs. Every minute, the script records a structured JSON event containing metadata about the run such as a unique execution ID, timestamp, hostname, environment, job name, status, and process information.

This pattern is useful for tracking scheduled jobs, QA runs, batch automation, and overall system health in a way that is easy to query from logs or files.

## What the Python script does

Each execution collects and writes a heartbeat event in JSON format. The record includes details such as:

- run_id: unique identifier for the execution
- timestamp_utc: UTC timestamp for the run
- job_name: name of the scheduled automation job
- environment: development, QA, or production
- hostname: EC2 instance name or hostname
- status: current execution status
- process_id: OS process ID for troubleshooting
- operating_system: OS details
- python_version: runtime version used during execution

The script is designed to be simple and reliable:

- structured JSON output
- proper error handling
- exit code 0 on success and 1 on failure
- logging compatible with systemd and journalctl

## Architecture

GitHub repository
        ↓ git clone / git pull
Amazon EC2 instance
        ↓
systemd timer runs every minute
        ↓
Python script emits a heartbeat event
        ↓
JSON line is appended to a log file
        ↓
Logs can be reviewed via journalctl and the output file

## Repository structure

```text
ec2-heartbeat-automation/
├── src/
│   └── heartbeat.py
├── tests/
│   └── test_heartbeat.py
├── systemd/
│   ├── heartbeat.service
│   └── heartbeat.timer
├── .gitignore
├── README.md
└── requirements.txt
```

## Python automation

### heartbeat.py

The heartbeat script is responsible for generating a single event each time it runs. In practice, this means it:

1. creates a unique run ID
2. captures the current UTC time
3. reads environment metadata
4. records the EC2 hostname and job context
5. writes a JSON object to the configured log file
6. exits with an appropriate status code

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

### test_heartbeat.py

The test suite checks that the script produces a valid heartbeat record by verifying:

- a valid GUID is generated
- a timestamp is generated
- required fields exist
- the execution status is successful

### requirements.txt

The automation itself uses Python's standard library. pytest is included only for testing support.

### .gitignore

Generated log files and environment-specific configuration should not be committed to version control.

## systemd service and timer notes

### heartbeat.service

Important details:

- Type=oneshot means the script runs once and exits after completion
- the service uses a dedicated Linux account instead of root
- ReadWritePaths restricts where the automation can write files
- output is sent to the Linux journal
- environment variables control configuration and runtime behavior

Replace YOUR-USERNAME with your actual GitHub username or service account as needed.

### heartbeat.timer

Persistent=true ensures the job is triggered again if the server was offline when the timer was scheduled to fire.

## Operational notes

- Keep log output small and structured so it is easy to search and analyze.
- Use consistent environment names across all EC2 instances to simplify filtering.
- Store logs in a known location so they can be reviewed with journalctl or custom monitoring tools.
- Treat the heartbeat as a lightweight health signal for automation jobs rather than as a full application telemetry system.

This setup gives you a simple, low-overhead way to confirm that scheduled automation is running correctly and to trace execution history over time.

## Key benefits

- lightweight monitoring for scheduled EC2 jobs
- simple JSON log records for troubleshooting and auditing
- no external dependencies required for the runtime script
- works well with systemd timers and journalctl
- easy to extend with custom fields for business or operational metadata

## Local development and testing

### 1. Create a virtual environment

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. On Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

You should see the prompt change to something like:

```powershell
(.venv) PS C:\Development_Folder\Python\ec2_heartbeat_automation>
```

### 3. Verify the environment

```powershell
dir .venv
dir .venv\Scripts
```

You should see Python-related files such as:

- activate
- Activate.ps1
- python.exe
- pip.exe

### 4. Validate the installation

```powershell
python --version
pip --version
```

### 5. Run the heartbeat locally

In Bash (including Linux and GitHub Codespaces), run:

```bash
OUTPUT_FILE="./events.jsonl" ENVIRONMENT="local" python src/heartbeat.py
```

In Windows PowerShell, run:

```powershell
$env:OUTPUT_FILE="./events.jsonl"
$env:ENVIRONMENT="local"
python .\src\heartbeat.py
```

Both commands append a heartbeat event to `events.jsonl` in the project directory.

### 6. Run tests

```bash
pytest -v
```

Run this after setting up the environment to check that the heartbeat code behaves as expected. The `-v` option enables verbose output, listing each test by name and showing whether it passed or failed. The tests verify the heartbeat's status and required fields, and check that its run ID and timestamp have valid formats.

If you want to install test tooling manually:

```powershell
pip install pytest
```

## Deployment notes

After the script is installed on an EC2 instance and configured with a systemd service and timer, it will emit heartbeat events automatically without requiring manual interaction or a long-running process.

This gives you a reliable operational check that the automation is still running, while also providing enough metadata to troubleshoot failures and understand execution history over time.

## Summary

The EC2 heartbeat automation is a small but practical monitoring pattern for scheduled work. It helps confirm that jobs are alive, captures execution context, and writes machine-readable records that can be searched in logs or parsed later for alerting, auditing, or operational analysis.