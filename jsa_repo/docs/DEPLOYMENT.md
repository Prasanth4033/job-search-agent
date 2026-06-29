# Deployment Guide

## Option A — Local Daemon (Recommended for personal use)

Run the agent as a long-lived background process on your machine.

```bash
# Terminal / background process
./scripts/run.sh --daemon &
```

The agent will:
- Run immediately on startup.
- Then fire every day at `schedule.run_time` (default 07:00 UTC).

To keep it running across reboots, add it to your shell startup or use a process manager.

### macOS — launchd

Create `~/Library/LaunchAgents/com.jobagent.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>             <string>com.jobagent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/full/path/to/job-search-agent/scripts/run.sh</string>
    <string>--daemon</string>
  </array>
  <key>RunAtLoad</key>         <true/>
  <key>KeepAlive</key>         <true/>
  <key>StandardOutPath</key>   <string>/tmp/jobagent.log</string>
  <key>StandardErrorPath</key> <string>/tmp/jobagent.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.jobagent.plist
```

### Linux — systemd

Create `/etc/systemd/system/job-search-agent.service`:

```ini
[Unit]
Description=Daily Job Search Agent
After=network.target

[Service]
Type=simple
User=<your-user>
WorkingDirectory=/path/to/job-search-agent
ExecStart=/bin/bash scripts/run.sh --daemon
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable job-search-agent
sudo systemctl start job-search-agent
sudo systemctl status job-search-agent
```

### Windows — Task Scheduler

1. Open **Task Scheduler** → **Create Basic Task**.
2. Trigger: **Daily** at **07:00**.
3. Action: **Start a program** → `python` with arguments `-m job_agent.main`.
4. Start in: `C:\path\to\job-search-agent`.

---

## Option B — Cron (Linux/macOS)

```bash
# Run daily at 07:00 UTC
0 7 * * * cd /path/to/job-search-agent && .venv/bin/python -m job_agent.main >> logs/cron.log 2>&1
```

Edit with `crontab -e`.

---

## Option C — Docker (Production / Server)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "job_agent.main", "--daemon"]
```

```bash
docker build -t job-search-agent .
docker run -d \
  -e EMAIL_SENDER=you@gmail.com \
  -e EMAIL_PASSWORD=your-app-password \
  -e EMAIL_RECIPIENT=gspr4033@gmail.com \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/logs:/app/logs \
  --name job-agent \
  --restart unless-stopped \
  job-search-agent
```

---

## Monitoring

- **Logs**: `logs/job_agent_YYYY-MM-DD.log` — rotates daily, 7-day retention.
- **Reports**: `reports/job_report_YYYY-MM-DD.html` — open in browser.
- **Email**: Delivered to `EMAIL_RECIPIENT` each morning.

### Check if daemon is alive

```bash
# systemd
sudo systemctl status job-search-agent

# Docker
docker logs --tail 50 job-agent

# Process
pgrep -f "job_agent.main"
```
