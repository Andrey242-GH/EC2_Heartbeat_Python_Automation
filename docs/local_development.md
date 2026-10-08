## Local Development

This guide sets up the project on your computer and starts the Flask dashboard. You can use any editor; [Visual Studio Code](https://code.visualstudio.com/) and [GitHub Codespaces](https://github.com/features/codespaces) are both suitable. The commands below assume Git and Python 3 are installed.

### 1. Create and open a project folder

First, create a folder on your computer to hold your projects. Then open that folder in Visual Studio Code. The repository will be cloned into this folder, creating its own project subfolder.

**Bash (Linux or macOS)**

```bash
mkdir -p "$HOME/projects"
cd "$HOME/projects"
code .
```

**PowerShell (Windows)**

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\projects" | Out-Null
Set-Location "$HOME\projects"
code .
```

The `code .` command opens the current folder in VS Code. If that command is not available, open VS Code, choose **File > Open Folder**, and select the `projects` folder you just created. Then open the integrated terminal with **Terminal > New Terminal**. Make sure the terminal is in the `projects` folder before continuing.

### 2. Clone the repository

In the VS Code integrated terminal, replace `<owner>` and `<repository>` with the GitHub account and repository name. These commands create a new repository folder inside `projects` and move into it.

**Bash (Linux or macOS)**

```bash
git clone https://github.com/<owner>/<repository>.git
cd <repository>
```

**PowerShell (Windows)**

```powershell
git clone https://github.com/<owner>/<repository>.git
Set-Location <repository>
```

### 3. Create a virtual environment and install dependencies

A virtual environment keeps this project's Python packages separate from other projects on your machine.

**Bash**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation because of the current process execution policy, allow scripts for this terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

When the environment is active, the terminal prompt usually shows `(.venv)`. Activate it again whenever you open a new terminal for this project.

### 4. Start the dashboard

Run the Flask development server from the repository root:

```bash
python src/app.py
```

The command is the same in Bash and PowerShell. Keep this terminal open while using the dashboard, then visit <http://127.0.0.1:5000>. The health endpoint is available at <http://127.0.0.1:5000/health>, and the event data is available at <http://127.0.0.1:5000/api/events>.

### 5. Generate a local heartbeat event

Open a second terminal in the repository and activate the virtual environment there. The commands below run the heartbeat once. Setting `OUTPUT_FILE` makes it write to the same `events.jsonl` file that the dashboard reads, instead of the Linux service's default `/var/lib/heartbeat/events.jsonl` path.

**Bash**

```bash
source .venv/bin/activate
OUTPUT_FILE="$PWD/events.jsonl" python src/heartbeat.py
```

**PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
$env:OUTPUT_FILE = Join-Path $PWD "events.jsonl"
python .\src\heartbeat.py
```

To generate a heartbeat repeatedly, wrap the command in a loop with a pause between runs. These examples create one event every minute. Stop either loop with `Ctrl+C`.

**Bash**

```bash
source .venv/bin/activate
until false; do
	OUTPUT_FILE="$PWD/events.jsonl" python src/heartbeat.py
	sleep 60
done
```

**PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
$env:OUTPUT_FILE = Join-Path $PWD "events.jsonl"
do {
		python .\src\heartbeat.py
		Start-Sleep -Seconds 60
} until ($false)
```

Refresh the dashboard to see the generated event. The app refreshes its event data when the page is loaded.

### 6. Run the tests

From the repository root with the virtual environment active:

```bash
python -m pytest
```

This command works in both Bash and PowerShell. A successful run reports the tests as passed.

### Stop the server and leave the environment

Press `Ctrl+C` in the terminal running Flask. To leave the virtual environment, use the matching command:

```bash
deactivate
```

`deactivate` works in both Bash and PowerShell after activating the environment.