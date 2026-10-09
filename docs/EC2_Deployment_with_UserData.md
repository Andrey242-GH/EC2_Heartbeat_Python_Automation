## Deploying with EC2 User Data

EC2 user data is a script that runs automatically the first time an instance starts. It can install the application and configure its services without requiring you to enter each command over SSH. The example below is for Amazon Linux 2023 and uses the project's systemd service files.

### Before you launch

Make sure you have:

- An Amazon Linux 2023 EC2 instance.
- A security group that allows SSH on port `22` from your IP address if you plan to connect over SSH.
- An inbound security-group rule for TCP port `5000` from your IP address if you want to open the dashboard in a browser.
- A GitHub repository that EC2 can access. The example repository is public. If you use your own repository, replace the URL below with its HTTPS URL.

When launching the instance in the AWS console, expand **Advanced details**, paste the script into **User data**, and then launch the instance. User data runs as `root`, so the script does not need `sudo` for administrative commands. The script uses `runuser` when it needs to create files or install packages as the restricted `heartbeat` account.

### User-data script

Review `REPO_URL` and `BRANCH` before launch. Use the branch that contains the version you want to deploy. To use `EC2_Flask_Dashboard`, change `BRANCH="main"` to `BRANCH="EC2_Flask_Dashboard"`. That branch must exist in the repository you selected.

```bash
#!/bin/bash
set -Eeuo pipefail

# Save script output so setup problems can be diagnosed after launch.
exec > >(tee -a /var/log/user-data.log) 2>&1

APP_DIR="/opt/EC2_Heartbeat_Python_Automation"
SERVICE_USER="heartbeat"
REPO_URL="https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git"
BRANCH="main"

echo "Starting EC2 Heartbeat Automation setup..."

# Install operating-system packages required to download and run the app.
dnf update -y
dnf install -y git python3 python3-pip

# Create the service account if it does not already exist.
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
	useradd \
		--system \
		--home-dir "$APP_DIR" \
		--shell /sbin/nologin \
		"$SERVICE_USER"
fi

# Download only the selected branch into the path expected by systemd.
git clone \
	--single-branch \
	--branch "$BRANCH" \
	"$REPO_URL" \
	"$APP_DIR"

# Let the service account read the app and manage its virtual environment.
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"
runuser -u "$SERVICE_USER" -- \
	python3 -m venv "$APP_DIR/.venv"

# Install the Python packages used by the dashboard and heartbeat job.
runuser -u "$SERVICE_USER" -- \
	"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
runuser -u "$SERVICE_USER" -- \
	"$APP_DIR/.venv/bin/python" -m pip install \
	-r "$APP_DIR/requirements.txt"

# Create storage that the heartbeat account can write to.
mkdir -p /var/lib/heartbeat
chown "$SERVICE_USER:$SERVICE_USER" /var/lib/heartbeat
chmod 750 /var/lib/heartbeat

# Run the tests before installing and starting the services (Optional).
cd "$APP_DIR"
runuser -u "$SERVICE_USER" -- \
	"$APP_DIR/.venv/bin/python" -m pytest -v

# Install the systemd unit files provided by the repository.
cp "$APP_DIR/systemd/heartbeat.service" \
	/etc/systemd/system/heartbeat.service
cp "$APP_DIR/systemd/heartbeat.timer" \
	/etc/systemd/system/heartbeat.timer
cp "$APP_DIR/systemd/heartbeat-web.service" \
	/etc/systemd/system/heartbeat-web.service

# Make systemd read the new units, run one heartbeat, and start the services.
systemctl daemon-reload
systemctl start heartbeat.service
systemctl enable --now heartbeat.timer
systemctl enable --now heartbeat-web.service

echo "Heartbeat automation deployment completed."
```

The script uses `set -Eeuo pipefail` so it stops if a command fails instead of printing a success message after an incomplete setup. The test suite runs before the systemd units are started; if a test fails, setup stops and the error is recorded in the user-data log. User data normally runs only during the instance's first launch, not every time you reboot it.

### Check the first-boot setup

Wait a few minutes after launching the instance, then connect to it using SSH or EC2 Instance Connect. Check the overall user-data result and its log:

```bash
sudo cloud-init status --long
sudo tail -n 100 /var/log/user-data.log
```

The log should end with `Heartbeat automation deployment completed.` If it does not, find the first command that reported an error and correct it before trying to start the services manually.

Check that the dashboard service is running and the heartbeat timer is scheduled:

```bash
sudo systemctl status heartbeat-web.service heartbeat.timer --no-pager
sudo systemctl list-timers --all | grep heartbeat
```

The dashboard should be `active (running)`. The timer should be `active (waiting)` and show its next run time. The heartbeat job itself is a one-shot service, so it can show `inactive (dead)` after it successfully finishes. Check its recent log and the event file to confirm it ran:

```bash
sudo journalctl \
	-u heartbeat.service \
	--since "10 minutes ago" \
	--no-pager

sudo tail -n 20 /var/lib/heartbeat/events.jsonl
```

The event file is created after the first successful heartbeat. If it does not exist yet, wait for the next timer run or start one manually with `sudo systemctl start heartbeat.service`.

## View the dashboard in a browser

The `heartbeat.py` script writes events to a file; it does not serve a web page itself. The Flask application in `app.py`, served by Gunicorn, provides the dashboard and API. The included web service listens on port `5000`, not the default HTTP port `80`.

After confirming `heartbeat-web.service` is running and the security group allows TCP port `5000` from your IP address, open this URL in a browser. Replace the placeholder with the instance's Public IPv4 address:

```text
http://EC2_PUBLIC_IP:5000/
```

The application also provides these endpoints:

- `/api/events` returns the recent heartbeat records as JSON.
- `/health` returns the application's health status.

For example, use `http://EC2_PUBLIC_IP:5000/health` to check the health endpoint. If the page cannot be reached, verify the instance's public IP, the port `5000` security-group rule, and the status/logs of `heartbeat-web.service`.