# Redeploy Changes to EC2

Use this guide after the application has already been installed on your EC2 instance and you have pushed new changes to GitHub. Run the commands in an SSH terminal connected to the EC2 instance, not in a terminal on your own computer.

The examples assume the project is installed at `/opt/EC2_Heartbeat_Python_Automation`, runs as the `heartbeat` account, and is deployed from the `main` branch. If you deployed a different branch, replace `main` in the pull command with that branch's name.

## 1. Check the server checkout

Before updating, confirm which branch the server is using and check for local changes:

```bash
sudo -u heartbeat git \
	-C /opt/EC2_Heartbeat_Python_Automation \
	branch --show-current

sudo -u heartbeat git \
	-C /opt/EC2_Heartbeat_Python_Automation \
	status --short
```

The first command prints the current branch. The second should print nothing when there are no uncommitted changes. If it lists files, stop and review them before updating; do not discard changes you need.

## 2. Download the pushed changes

Pull the latest commit from GitHub:

```bash
sudo -u heartbeat git \
	-C /opt/EC2_Heartbeat_Python_Automation \
	pull --ff-only origin main
```

`--ff-only` updates the checkout only when Git can apply the changes without creating a merge commit. If Git reports that it cannot fast-forward, stop and resolve the branch difference rather than forcing the update.

## 3. Update dependencies and run tests

If the update changed `requirements.txt`, install the updated packages into the existing virtual environment. It is also safe to run this after every update:

```bash
sudo -u heartbeat \
	/opt/EC2_Heartbeat_Python_Automation/.venv/bin/python -m pip \
	install -r \
	/opt/EC2_Heartbeat_Python_Automation/requirements.txt
```

Run the tests before restarting the application:

```bash
cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

Continue when the tests pass. If a test fails, read the output and fix the problem before proceeding.

## 4. Restart the application

After updating application code, restart the dashboard so it loads the new code:

```bash
sudo systemctl restart heartbeat-web.service
```

The scheduled heartbeat script uses the updated files the next time the timer runs. You do not need to restart the timer just because Python source code changed.

### If a systemd unit file changed

If you changed any file under the repository's `systemd/` directory, copy the updated unit file to `/etc/systemd/system/` and tell systemd to reload its configuration. For example, to copy all three unit files:

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
sudo systemctl restart heartbeat-web.service
```

If only one unit file changed, you can copy only that file. `daemon-reload` makes systemd reread the unit definitions. Restart the timer or dashboard service after changing its unit so the updated settings take effect. `heartbeat.service` is a one-shot job; its updated settings are used the next time it runs.

## 5. Verify the deployment

Check whether the dashboard and timer are running and configured to start after a reboot:

```bash
sudo systemctl status heartbeat-web.service heartbeat.timer --no-pager
sudo systemctl is-enabled heartbeat-web.service heartbeat.timer
sudo systemctl list-timers --all | grep heartbeat
```

The dashboard should show `active (running)`, and the timer should show `active (waiting)` with its next run time. `is-enabled` should report `enabled` for both services.

Check the dashboard's local health endpoint:

```bash
curl --fail http://127.0.0.1:5000/health
```

To inspect recent application and heartbeat logs:

```bash
sudo journalctl -u heartbeat-web.service -n 50 --no-pager
sudo journalctl -u heartbeat.service --since "10 minutes ago" --no-pager
```

To confirm that heartbeat events are being written:

```bash
sudo tail -n 10 /var/lib/heartbeat/events.jsonl
```

The event file may not exist until the first successful scheduled heartbeat. If a service is not active or the health check fails, use the journal output to find the error before retrying the deployment.
