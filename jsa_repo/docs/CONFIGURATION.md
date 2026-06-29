# Configuration Guide

All configuration lives in two files:

| File | Purpose | Commit to git? |
|---|---|---|
| `config.yaml` | Non-secret settings (schedule, skills, sources) | **No** (in `.gitignore`) |
| `.env` | Secrets (email password) | **Never** |

Copy the example files before first use:

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

---

## config.yaml Reference

```yaml
schedule:
  run_time: "07:00"      # 24-hour UTC — when daemon mode fires each day
```

```yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  sender: "you@gmail.com"
  password: ""           # Set in .env instead
  recipient: "gspr4033@gmail.com"
```

```yaml
scrapers:
  request_timeout_sec: 15   # Per-request timeout
  retry_attempts: 3         # Retries on 5xx / connection errors
  parallel_workers: 3       # Concurrent scraper threads
```

```yaml
filters:
  hours_window: 24          # Rolling window — jobs older than this are excluded
  us_only: true             # Reject non-US locations
```

```yaml
skills:
  - "AWS Data Engineer"
  - "Hadoop Data Engineer"
  # Add or remove as needed
```

```yaml
sources:
  randstad:
    enabled: true
  manpower:
    enabled: true
  kelly:
    enabled: true
  teamlease:
    enabled: true           # Set false to skip
  abc_consultants:
    enabled: true
```

---

## .env Reference

```dotenv
EMAIL_SENDER=you@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   # 16-char Gmail App Password
EMAIL_RECIPIENT=gspr4033@gmail.com
SMTP_HOST=smtp.gmail.com             # Optional override
SMTP_PORT=587                        # Optional override
```

### Generating a Gmail App Password

1. Sign in to [myaccount.google.com](https://myaccount.google.com).
2. Navigate to **Security → 2-Step Verification** — ensure it is **on**.
3. Navigate to **Security → App passwords**.
4. Select app: **Mail**, device: **Other** → type "Job Search Agent".
5. Click **Generate** and copy the 16-character password.
6. Paste it as `EMAIL_PASSWORD` in your `.env`.

> **Important:** Use the App Password (format: `xxxx xxxx xxxx xxxx`), not your Google account password.

---

## Environment Variable Precedence

Environment variables always **override** values in `config.yaml`.  
Order of precedence (highest first):

1. Shell environment variables (`export EMAIL_SENDER=...`)
2. `.env` file
3. `config.yaml`
4. Hardcoded defaults in `job_agent/config.py`

---

## CLI Flags (override config at runtime)

| Flag | Default | Effect |
|---|---|---|
| `--hours N` | `24` | Change the recency window to N hours |
| `--no-email` | off | Skip email; save HTML report only |
| `--daemon` | off | Run continuously, firing daily at `schedule.run_time` |
