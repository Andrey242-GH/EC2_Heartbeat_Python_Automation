# Troubleshooting

Use this guide to diagnose common local and EC2 problems. On EC2, run the commands in an SSH session. The installation and redeployment walkthroughs are in [EC2 deployment](EC2_Deployment.md), [EC2 deployment with User Data](EC2_Deployment_with_UserData.md), and [EC2 redeployment](EC2_Redeployment.md).

## Dashboard will not open

First check whether the dashboard service is running and inspect its recent logs:

```bash
sudo systemctl status heartbeat-web.service --no-pager
sudo journalctl -u heartbeat-web.service -n 50 --no-pager
```

Test the health endpoint from the EC2 instance itself:

```bash
curl --fail http://127.0.0.1:5000/health
```

If this local request fails, use the service logs to diagnose the application. If it succeeds locally but your browser cannot connect, check that you are using `http://EC2_PUBLIC_IP:5000/` and that the EC2 security group allows TCP port `5000` from your IP address. Port `80` is not used by this setup.

## Gunicorn is missing or the dashboard service fails to start

The dashboard service starts Gunicorn from the project's virtual environment. Check whether that executable exists:

```bash
ls -l /opt/EC2_Heartbeat_Python_Automation/.venv/bin/gunicorn
```

This project lists Gunicorn in `requirements.txt`. Install the project's declared dependencies into the same virtual environment used by systemd, then restart the dashboard:

```bash
sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python -m pip \
  install -r \
  /opt/EC2_Heartbeat_Python_Automation/requirements.txt
sudo systemctl restart heartbeat-web.service
```

If the install reports success but Gunicorn is still missing, confirm that you deployed the expected branch and that the service points to this virtual environment. Prefer fixing `requirements.txt` and redeploying if the dependency is missing from your branch; installing packages manually without updating the requirements file will not make future deployments reproducible.

## No heartbeat events appear

Check whether the timer is scheduled and inspect the heartbeat service logs:

```bash
sudo systemctl list-timers --all | grep heartbeat
sudo journalctl -u heartbeat.service --since "10 minutes ago" --no-pager
```

You can trigger one run immediately to help diagnose the issue:

```bash
sudo systemctl start heartbeat.service
sudo journalctl -u heartbeat.service -n 20 --no-pager
```

Then check the event file:

```bash
sudo tail -n 10 /var/lib/heartbeat/events.jsonl
```

The file is created after the first successful run. `heartbeat.service` is a one-shot job, so it may show `inactive (dead)` after it completes successfully; use the journal output to confirm the result. If the log reports a permission error, check that `/var/lib/heartbeat` exists and is owned by the `heartbeat` account.

## Dashboard shows no events

The dashboard and heartbeat writer must read and write the same JSONL file. Under the EC2 systemd services, both are configured to use `/var/lib/heartbeat/events.jsonl`. For local development, the heartbeat script and Flask app have different default output paths, so set `OUTPUT_FILE` to the same path for both commands. For example, use `OUTPUT_FILE="$PWD/events.jsonl"` when starting each process from the project directory.

If the paths match, confirm that the event file exists and contains valid JSONL records. Each line should be a separate JSON object.

## EC2 User Data setup did not finish

User Data normally runs only during the instance's first launch. Check cloud-init status and the saved script output:

```bash
sudo cloud-init status --long
sudo tail -n 100 /var/log/user-data.log
```

Find the first command that failed in the log. Correct that cause before manually retrying the setup; rerunning the whole script can fail if the repository or service files have already been created.

## Tests fail

Run the tests from the repository root using the project's virtual environment:

```bash
python -m pytest -v
```

On EC2, run them as the service account with the deployed virtual environment:

```bash
cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

Read the first failure and resolve it before enabling or restarting the scheduled service.
