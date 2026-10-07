# EC2 Heartbeat Automation

This project creates a lightweight heartbeat for EC2-based automation jobs. Every minute, the script records a structured JSON event containing metadata about the run, including a unique execution ID, timestamp, hostname, environment, job name, status, and process information.

This pattern is useful for tracking scheduled jobs, QA runs, batch automation, and overall system health in a way that is easy to query from logs or files.

## What the Python script does

Each execution collects and writes a heartbeat event in JSON format. The record includes:

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

## Python automation

### app.py

`app.py` is the small Flask web application that turns the heartbeat log into a live dashboard. It reads the JSON records from `events.jsonl`, sorts them newest-first, and serves them in a browser-friendly format.

It provides three useful endpoints:

- `/` displays the dashboard page with a table of recent EC2 job runs
- `/api/events` returns the same event data as JSON for scripts or monitoring tools
- `/health` reports the application status so it can be checked by a load balancer or a quick curl command

This file is the web-facing part of the project. The actual heartbeat job still runs separately in `heartbeat.py`; `app.py` simply reads and displays the data.

### heartbeat.py

The heartbeat script is responsible for generating a single event each time it runs. In practice, it:

1. creates a unique run ID
2. captures the current UTC time
3. reads environment metadata
4. records the EC2 hostname and job context
5. writes a JSON object to the configured log file
6. exits with an appropriate status code

This script is intentionally lightweight and safe for scheduled automation. It writes one JSON object per execution, which makes it easy to review logs later or feed into monitoring systems.

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

## index.html

`index.html` is the dashboard page that users see in the browser. It uses the events passed from `app.py` to build a table showing recent heartbeat activity, including the run ID, timestamp, job name, status, environment, hostname, and process ID.

It also includes a live refresh so the page updates automatically every 10 seconds, which is helpful when you're watching a fleet of automation jobs in real time. If there are no heartbeat events yet, the page shows a friendly empty-state message instead of a blank table.

### test_heartbeat.py

The test suite verifies that the script produces a valid heartbeat record by checking:

- a valid GUID is generated
- a timestamp is generated
- required fields exist
- the execution status is successful

### requirements.txt

This file tracks the Python packages required by the project. The core heartbeat script uses Python's standard library, but the web dashboard introduces a dependency on Flask and Gunicorn. After adding the dashboard, you should keep the package list current with commands such as:

```bash
python -m pip install flask gunicorn
python -m pip freeze > requirements.txt
```

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

The checked-in service runs as the dedicated `heartbeat` account and uses the paths shown in the deployment instructions below.

### heartbeat.timer

`Persistent=true` ensures the job is triggered again if the server was offline when the timer was scheduled to fire.

### heartbeat-web.service

This systemd unit starts the Flask app with Gunicorn so the dashboard stays running in the background. It binds the app to port 5000, points at the same `events.jsonl` file used by the heartbeat job, and restarts automatically if it crashes. In other words, `heartbeat-web.service` is what makes the web monitoring page available to anyone browsing the EC2 instance.

## Operational notes

- Keep log output small and structured so it is easy to search and analyze.
- Use consistent environment names across all EC2 instances to simplify filtering.
- Store logs in a known location so they can be reviewed with `journalctl` or custom monitoring tools.
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

After the initial heartbeat script was working, I noticed there was no easy way to view the generated events from a browser. To solve that, I added a lightweight Flask dashboard, which is why the project now includes the web app and the Flask dependency.

```text
If needed, install the dashboard dependencies:

python -m pip install flask gunicorn

To save the current dependencies:

python -m pip freeze > requirements.txt
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
(.venv) PS C:\Development_Folder\Python\EC2_Heartbeat_Python_Automation>
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

Run this after setting up the environment to check that the heartbeat code behaves as expected. The `-v` option enables verbose output, listing each test by name and showing whether it passed or failed. The tests verify the heartbeat status and required fields, and check that the run ID and timestamp have valid formats.

If you want to install test tooling manually:

```powershell
pip install pytest
```

## EC2 deployment

These steps install the application on Amazon Linux and configure `systemd` to run it once per minute. They assume the repository is publicly accessible and use the `heartbeat` service account and file paths configured in the included unit files.

### 1. Launch and connect to an EC2 instance

In the AWS console:

1. Open **EC2** and choose **Launch instance**.
2. Choose an Amazon Linux AMI, such as Amazon Linux 2023.
3. Select an instance type appropriate for your account and workload.
4. Create or select a key pair if you plan to connect over SSH.
5. In the security group, allow inbound SSH (TCP port `22`) only from your current IP address if using SSH.
6. Launch the instance.

This application does not host a website or API. Do not open inbound ports `80`, `443`, `5000`, or `8000`. If connecting through EC2 Instance Connect or Session Manager, follow the AWS setup requirements for that method; you can skip the local SSH commands, and you may not need an inbound SSH rule.

To connect from a Bash terminal using SSH:

```bash
chmod 400 my-ec2-key.pem
ssh -i my-ec2-key.pem ec2-user@EC2_PUBLIC_IP
```

Replace `my-ec2-key.pem` with the path to your downloaded private key and `EC2_PUBLIC_IP` with the instance’s public IP address. Run these commands on your own computer, not inside the EC2 shell.

### 2. Install the application

Run the following commands after connecting to the instance. This account is used to run the service without root privileges.

```bash
sudo dnf update -y
sudo dnf install -y git python3

sudo useradd \
  --system \
  --home-dir /opt/EC2_Heartbeat_Python_Automation \
  --shell /sbin/nologin \
  heartbeat

# this is to check it got created

id heartbeat

# This is to copy the main branch (either one)

sudo git clone \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation

# This is to copy the data from another branch other than main (either one)

sudo git clone \
  --single-branch \
  --branch EC2_Flask_Dashboard \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation

sudo chown -R \
  heartbeat:heartbeat \
  /opt/EC2_Heartbeat_Python_Automation

sudo -u heartbeat \
  python3 -m venv \
  /opt/EC2_Heartbeat_Python_Automation/.venv

sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python -m pip \
  install -r \
  /opt/EC2_Heartbeat_Python_Automation/requirements.txt
```

Create the event log directory. The service account needs write access because the script appends events there.

```bash
sudo mkdir -p /var/lib/heartbeat
sudo chown heartbeat:heartbeat /var/lib/heartbeat
sudo chmod 750 /var/lib/heartbeat
```

Run the tests before enabling the scheduled job:

```bash
cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

### 3. Install and enable the systemd timer

Copy the service and timer definitions from the repository, then reload systemd:

```bash
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.service \
  /etc/systemd/system/heartbeat.service
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.timer \
  /etc/systemd/system/heartbeat.timer

sudo systemctl daemon-reload
```

Run the service once manually to confirm it can write output, then enable the timer:

```bash
sudo systemctl start heartbeat.service
sudo systemctl status heartbeat.service --no-pager
sudo systemctl enable --now heartbeat.timer
```

The timer is configured to run the service once per minute. A successful one-shot service may show as `inactive (dead)` after it finishes; check its result and output rather than expecting it to remain running.

### 4. Verify and troubleshoot

Check when the next run is scheduled:

```bash
systemctl list-timers --all | grep heartbeat
```

Inspect recent JSON events:

```bash
sudo tail -n 10 /var/lib/heartbeat/events.jsonl
```

Read recent service logs:

```bash
sudo journalctl -u heartbeat.service --since "10 minutes ago" --no-pager
```

If a run fails, inspect the journal for the error, confirm that the virtual environment exists, and check that `/var/lib/heartbeat` is writable by the `heartbeat` account.

### 5. Deploy later repository changes

After pushing changes to the repository, connect to the instance and update the checkout. These commands assume the default branch is `main`.

```bash
sudo -u heartbeat git \
  -C /opt/EC2_Heartbeat_Python_Automation \
  pull --ff-only origin main

sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python -m pip \
  install -r \
  /opt/EC2_Heartbeat_Python_Automation/requirements.txt

cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

If the update changes either systemd unit file, copy the updated file(s) to `/etc/systemd/system/` and reload systemd:

```bash
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.service \
  /etc/systemd/system/heartbeat.service
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.timer \
  /etc/systemd/system/heartbeat.timer
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat-web.service \
  /etc/systemd/system/heartbeat-web.service
sudo systemctl daemon-reload
sudo systemctl restart heartbeat.timer
sudo systemctl enable --now heartbeat-web.service
```

## Deploying with EC2 user data

EC2 user data can automate the initial setup when an instance launches. The following example is for an Amazon Linux instance using `dnf`. It installs the required packages, configures the `heartbeat` service account and Python environment, runs the tests, and enables the systemd timer.

```bash
#!/bin/bash

# Log user-data output for troubleshooting.
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "Starting EC2 Heartbeat Automation setup..."

# Update the operating system and install dependencies.
dnf update -y
dnf install -y git python3

# Create a dedicated service account.
useradd \
  --system \
  --home-dir /opt/EC2_Heartbeat_Python_Automation \
  --shell /sbin/nologin \
  heartbeat || true

# Clone the repository.
git clone \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation

# Set repository ownership.
chown -R heartbeat:heartbeat \
  /opt/EC2_Heartbeat_Python_Automation

# Create a Python virtual environment.
sudo -u heartbeat \
  python3 -m venv \
  /opt/EC2_Heartbeat_Python_Automation/.venv

# Install Python requirements.
sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python \
  -m pip install --upgrade pip

sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python \
  -m pip install -r \
  /opt/EC2_Heartbeat_Python_Automation/requirements.txt

# Create the directory used to store heartbeat events.
mkdir -p /var/lib/heartbeat
chown heartbeat:heartbeat /var/lib/heartbeat
chmod 750 /var/lib/heartbeat

# Run the test suite (Optional). this action is for testing and it may cause problems
cd /opt/EC2_Heartbeat_Python_Automation

sudo -u heartbeat \
  .venv/bin/python -m pytest -v

# Install the systemd service and timer.
cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.service \
  /etc/systemd/system/heartbeat.service

cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.timer \
  /etc/systemd/system/heartbeat.timer

cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat-web.service \
  /etc/systemd/system/heartbeat-web.service

# Reload systemd, run the service once, and enable the recurring timer.
systemctl daemon-reload

systemctl start heartbeat.service
systemctl enable --now heartbeat.timer

systemctl enable --now heartbeat-web.service

echo "Heartbeat automation deployment completed."
```

You can also clone a specific branch instead of the default branch:

```bash
git clone \
  --single-branch \
  --branch EC2_Flask_Dashboard \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation
```

Instead of:

```bash
git clone \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation
```

User data runs during instance initialization. Its output is written to `/var/log/user-data.log`. After the instance launches, connect to it and use the following commands to verify the deployment.

### Confirm that the timer is scheduled

```bash
systemctl list-timers --all | grep heartbeat
```

### Check the timer and service status

```bash
sudo systemctl status heartbeat.timer
sudo systemctl status heartbeat.service
```

### Inspect generated heartbeat events

```bash
sudo tail -n 20 /var/lib/heartbeat/events.jsonl
```

### Review recent service logs

```bash
sudo journalctl \
  -u heartbeat.service \
  --since "10 minutes ago" \
  --no-pager
```

## View output in a browser

If you want to open your EC2 Public IPv4 address in a browser and view the Python automation output, your script must be running as a web application.

Right now, the `heartbeat.py` script only writes to a file. There is nothing listening on port `80`, so you will likely see one of the following:

- Connection refused
- Timeout
- Nginx default page (if Nginx is installed)
- Blank page

This is why the project includes `app.py`, which runs a Flask web application.

The application provides three endpoints:

- `/` — web dashboard
- `/api/events` — raw JSON records
- `/health` — application health check

## Test it in Codespaces

Install the requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Generate several records:

```bash
OUTPUT_FILE="./events.jsonl" \
ENVIRONMENT="codespaces" \
JOB_NAME="guid-heartbeat" \
python src/heartbeat.py
```

Then launch the Flask application:

```bash
OUTPUT_FILE="./events.jsonl" python src/app.py
```

For testing only, open a second Codespaces terminal and run:

```bash
while true
do
    OUTPUT_FILE="./events.jsonl" \
    ENVIRONMENT="codespaces" \
    JOB_NAME="guid-heartbeat" \
    python src/heartbeat.py

    sleep 10
done
```

## Update the EC2 installation

On EC2, pull your changes:

```bash
sudo -u heartbeat git \
  -C /opt/EC2_Heartbeat_Python_Automation \
  pull --ff-only origin main
```

Install requirements:

```bash
sudo -u heartbeat \
/opt/EC2_Heartbeat_Python_Automation/.venv/bin/python \
-m pip install \
-r /opt/EC2_Heartbeat_Python_Automation/requirements.txt
```

Copy all three service files:

```bash
sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.service \
  /etc/systemd/system/heartbeat.service

sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat.timer \
  /etc/systemd/system/heartbeat.timer

sudo cp \
  /opt/EC2_Heartbeat_Python_Automation/systemd/heartbeat-web.service \
  /etc/systemd/system/heartbeat-web.service
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable the timer and web application:

```bash
sudo systemctl enable --now heartbeat.timer
sudo systemctl enable --now heartbeat-web.service
```

Verify both parts:

Check the timer:

```bash
systemctl list-timers --all | grep heartbeat
```

Check the scheduled job:

```bash
sudo systemctl status heartbeat.service --no-pager
```

Check the web application:

```bash
sudo systemctl status heartbeat-web.service --no-pager
```

Check the saved events:

```bash
sudo tail -n 10 /var/lib/heartbeat/events.jsonl
```

Test the website from inside EC2:

```bash
curl http://localhost:5000/health
```

Expected response:

```json
{
  "application": "ec2-heartbeat-automation",
  "output_file": "/var/lib/heartbeat/events.jsonl",
  "status": "healthy"
}
```

Check whether port 5000 is listening:

```bash
sudo ss -ltnp | grep 5000
```

### Add the EC2 inbound rule

For initial testing, add this inbound rule to the EC2 security group:

- Type: Custom TCP
- Protocol: TCP
- Port: 5000
- Source: My IP
- Description: Heartbeat dashboard testing

Using My IP limits access to your current public IP.

Then open:

```text
http://YOUR_EC2_PUBLIC_IPV4:5000
```

Do not open only port 80 yet. For this setup, you must add `:5000`.

i found a problem and it was that the gunicorn was not installed so I first entered 

```bash
ls -l /opt/EC2_Heartbeat_Python_Automation/.venv/bin/gunicorn
```

and i got this "No such file or directory"

so i run this:

```bash
sudo -u heartbeat \
/opt/EC2_Heartbeat_Python_Automation/.venv/bin/pip \
install gunicorn flask
```

and it worked

## Summary

The EC2 heartbeat automation is a small but practical monitoring pattern for scheduled work. It helps confirm that jobs are alive, captures execution context, and writes machine-readable records that can be searched in logs or parsed later for alerting, auditing, or operational analysis.
