## EC2 deployment

This section explains how to launch an Amazon EC2 virtual machine and connect to it. The steps assume an Amazon Linux instance and a repository that you can access.

### 1. Launch an EC2 instance

In the AWS Management Console:

1. Sign in to AWS, open **EC2**, and choose **Launch instance**.
2. Enter a name for the instance so you can recognize it later.
3. Under **Application and OS Images**, choose an Amazon Linux image, such as Amazon Linux 2023.
4. Choose an instance type. For learning and testing, use an eligible low-cost or free-tier option if available to your account.
5. Under **Key pair (login)**, create or select a key pair if you plan to connect from your computer with SSH. Download and keep the `.pem` private key somewhere secure; AWS does not let you download it again later.
6. Under **Network settings**, create or select a security group. Add an inbound rule for SSH: type **SSH**, port `22`, source **My IP**. This allows SSH connections from your current public IP address only.
7. Review the settings and choose **Launch instance**.

After launch, open **EC2 > Instances** and select the new instance. Wait until its instance state is **Running** and its status checks have passed. In the instance details, find and copy its **Public IPv4 address**. You will use this address to connect.

### 2. Allow dashboard access for testing

The dashboard uses port `5000`. Add an inbound rule for this port only if you need to open the dashboard directly in a browser for testing. Keep the source set to **My IP** so the dashboard is not exposed to everyone on the internet. This rule is separate from SSH on port `22`.

To add the rule after the instance has been created:

1. In the EC2 console, choose **Instances** in the left navigation and select your instance.
2. On the instance details page, open the **Security** tab.
3. Under **Security groups**, choose the security group name linked to the instance.
4. Open **Inbound rules** and choose **Edit inbound rules**.
5. Choose **Add rule**, then set **Type** to **Custom TCP**. Set **Port range** to `5000`, **Source** to **My IP**, and add a description such as `Heartbeat dashboard testing`.
6. Choose **Save rules**.

If you are not testing the dashboard in a browser, you can skip this port `5000` rule. Do not use `0.0.0.0/0` as the source for this testing rule; that would allow connections from any IP address.

### 3. Connect to the instance

You can connect either from the AWS console or from a terminal on your computer.

#### Option A: Connect in the AWS console

1. Go to **EC2 > Instances** and select your running instance.
2. Choose **Connect** near the top of the page.
3. Open the **EC2 Instance Connect** tab and choose **Connect**.

If the EC2 Instance Connect option is unavailable or the connection fails, use SSH from a terminal instead.

#### Option B: Connect using SSH

First open a terminal and change directory to the folder containing your `.pem` key. For example, if the key is in your Downloads folder:

**Bash (Linux or macOS)**

```bash
cd "$HOME/Downloads"
chmod 400 my-ec2-key.pem
ssh -i my-ec2-key.pem ec2-user@EC2_PUBLIC_IP
```

**PowerShell (Windows)**

```powershell
Set-Location "$HOME\Downloads"
ssh -i .\my-ec2-key.pem ec2-user@EC2_PUBLIC_IP
```

Before running the command, replace `my-ec2-key.pem` with your key's actual filename and replace `EC2_PUBLIC_IP` with the instance's **Public IPv4 address**. Keep the key filename and IP address together with the `-i` and SSH destination as shown. The first time you connect, SSH may ask whether you trust the host; type `yes` if the displayed address matches your EC2 instance.

When the connection succeeds, your terminal is now running commands on the EC2 instance. Type `exit` and press Enter when you want to disconnect.
otheriwse go to the ec2 instance and click on connect 


### 4. Install the application

Run these commands in the EC2 terminal after connecting. You are now working on the Amazon Linux server, not on your own computer. The commands prepare Git and Python, create the restricted `heartbeat` service account, download the project, and install its Python packages.

#### 4.1 Install Git and Python

`dnf` is the package manager used by Amazon Linux 2023. The first command installs available system updates; the second installs Git and Python, which are needed to download and run the application.

```bash
sudo dnf update -y
sudo dnf install -y git python3 python3-pip
```

#### 4.2 Create the service account

The application services run as the `heartbeat` account instead of as the administrator (`root`). This limits the permissions available to the application. Create the account once, then use `id` to confirm it exists:

```bash

sudo useradd \
  --system \
  --home-dir /opt/EC2_Heartbeat_Python_Automation \
  --shell /sbin/nologin \
  heartbeat

id heartbeat
```

The `useradd` command should only be run once. If it reports that `heartbeat` already exists, run `id heartbeat`; if that prints the account details, continue to the next step.

#### 4.3 Download the project

Use the repository URL for the copy of the project you want to deploy. If you created a new repository in your own GitHub account and put the project in it, open that repository on GitHub, choose **Code**, and copy its HTTPS URL. Replace the `https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git` URL in the command you choose with your copied URL. If you did not create your own repository, leave the URL in the examples as it is.

Choose **one** of the commands below. Both download the repository into `/opt/EC2_Heartbeat_Python_Automation`; do not run both, or the second command will fail because that folder already exists.

- To download the repository's `main` branch:

```bash
sudo git clone \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation
```

- To download the `EC2_Flask_Dashboard` branch instead:

```bash
sudo git clone \
  --single-branch \
  --branch EC2_Flask_Dashboard \
  https://github.com/Andrey242-GH/EC2_Heartbeat_Python_Automation.git \
  /opt/EC2_Heartbeat_Python_Automation
```

`git clone` copies the project files to the server. `--branch` selects which version of the project to download, and `--single-branch` avoids downloading the other branches. The service files expect the project to be at `/opt/EC2_Heartbeat_Python_Automation`.

```text
If `git clone` fails, read the error and correct the cause first. Common causes include a misspelled repository URL, a branch name that does not exist, or a network problem. Deleting the folder will not fix those issues.

Only if the clone left an incomplete folder, and you have confirmed it contains no files or changes you need, you can remove that folder and try again. First check that the path is correct:


sudo ls -la /opt/EC2_Heartbeat_Python_Automation


If you are certain this is only the incomplete project download, remove it with:


sudo rm -rf -- /opt/EC2_Heartbeat_Python_Automation


**Warning:** `rm -rf` permanently deletes the folder and everything inside it. Double-check the path before running the command. Then rerun only the `git clone` command for the branch you want.
```

#### 4.4 Set project ownership and install Python packages

The systemd services run as the `heartbeat` account, not as `root`. The `git clone` command used `sudo`, so the downloaded files are owned by `root`. Change the project folder's owner and group to `heartbeat` so that account can use the project and create its virtual environment. The `-R` option applies the ownership change to everything inside the project folder as well.

```bash
sudo chown -R \
  heartbeat:heartbeat \
  /opt/EC2_Heartbeat_Python_Automation
```

Next, create the virtual environment and install the packages listed in `requirements.txt`. `sudo -u heartbeat` runs each command as the service account, so the virtual environment and installed packages are available to the services that use that account.

```bash
sudo -u heartbeat \
  python3 -m venv \
  /opt/EC2_Heartbeat_Python_Automation/.venv

sudo -u heartbeat \
  /opt/EC2_Heartbeat_Python_Automation/.venv/bin/python -m pip \
  install -r \
  /opt/EC2_Heartbeat_Python_Automation/requirements.txt
```

The first command creates an isolated Python environment at `.venv`. The second uses that environment's Python and `pip` to install the project's dependencies, including Flask and Gunicorn.

#### 4.5 Create the event log directory

The heartbeat writes events to `/var/lib/heartbeat/events.jsonl`. Create the parent directory, assign it to the service account, and restrict access so the service can write its event log without making the directory accessible to every user on the server.

```bash
sudo mkdir -p /var/lib/heartbeat
sudo chown heartbeat:heartbeat /var/lib/heartbeat
sudo chmod 750 /var/lib/heartbeat
```

`mkdir -p` creates the directory if it does not already exist. `chown` makes `heartbeat` the owner and group. The `750` permission gives the owner full access, allows the group to list and enter the directory, and gives other users no access. Because the service runs as `heartbeat`, it can create and append to the event file.

#### 4.6 (Optional) Test the application before scheduling it

Run the automated test before enabling the scheduled heartbeat. The test checks that the application can create a heartbeat event with the expected fields and valid ID and timestamp. It runs as the `heartbeat` account, matching the account used by the systemd service.

```bash
cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

The `cd` command moves into the project folder. The next command uses Python from the project's virtual environment to run `pytest`; `-v` prints the name and result of each test. A successful run should finish with `1 passed`. If a test fails, read the error output and fix the problem before enabling the scheduled job.

This is a code test only. It does not enable or test the systemd timer, start the dashboard, or check that the dashboard is reachable from your browser.

```bash
cd /opt/EC2_Heartbeat_Python_Automation
sudo -u heartbeat .venv/bin/python -m pytest -v
```

### 4.7 Install and enable the systemd services

The repository includes three systemd unit files: `heartbeat.service` runs the event-generation script once, `heartbeat.timer` schedules that job once per minute, and `heartbeat-web.service` keeps the dashboard running. Copy the unit files into systemd's configuration folder, then tell systemd to reload its configuration so it recognizes them:

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
```

Enable and start the timer and dashboard service:

```bash
sudo systemctl enable --now heartbeat.timer
sudo systemctl enable --now heartbeat-web.service
```

`enable` configures each unit to start automatically when the server boots. `--now` also starts it immediately. The timer will run `heartbeat.service` once per minute; the web service starts the dashboard and should stay running.

Check that both are running:

```bash
sudo systemctl status heartbeat.timer heartbeat-web.service --no-pager
sudo systemctl list-timers heartbeat.timer
```

The timer should show as `active (waiting)` and appear in the timer list with its next run time. The dashboard service should show as `active (running)`. To open the dashboard, visit `http://EC2_PUBLIC_IP:5000` in your browser, replacing `EC2_PUBLIC_IP` with the instance's public IPv4 address. Port `5000` must be allowed in the instance's security group, as described in section 2.

To run one heartbeat immediately rather than waiting for the next scheduled minute, start the one-shot service manually and inspect its log:

```bash
sudo systemctl start heartbeat.service
sudo journalctl -u heartbeat.service -n 20 --no-pager
```

`heartbeat.service` is a one-shot job: it exits after creating an event. For that reason, it may show `inactive (dead)` after a successful run. Check the journal for a success message. If the timer or dashboard service fails to start, inspect its recent log output with `sudo journalctl -u heartbeat.timer -n 50 --no-pager` or `sudo journalctl -u heartbeat-web.service -n 50 --no-pager`.

#### Verify and troubleshoot heartbeat runs

To see all heartbeat timers, including timers that are not currently active, run:

```bash
sudo systemctl list-timers --all | grep heartbeat
```

After the heartbeat has run successfully, inspect the latest event records:

```bash
sudo tail -n 10 /var/lib/heartbeat/events.jsonl
```

The event file is created on the first successful run, so it may not exist yet if the timer has not run. To review recent output from the heartbeat job when troubleshooting, run:

```bash
sudo journalctl -u heartbeat.service --since "10 minutes ago" --no-pager
```