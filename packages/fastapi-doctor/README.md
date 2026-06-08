# fastapi-therapist

Diagnose FastAPI codebases for security, performance, correctness, and architecture issues. Outputs a 0–100 health score.

## Installation

```bash
pip install fastapi-therapist
```

## Usage

```bash
# Full scan with verbose output
fastapi-therapist . --verbose

# Only scan changed files (git diff vs main)
fastapi-therapist . --diff

# Only scan staged files (pre-commit hook)
fastapi-therapist . --staged

# Output only the score (useful for CI)
fastapi-therapist . --score

# Install skill for AI coding agents (OpenCode, Claude, Cursor, etc.)
fastapi-therapist install
```

## Configuration

Suppress rules or skip files via `pyproject.toml` or `fastapi-doctor.config.json`:

```toml
# pyproject.toml
[tool.fastapi-doctor.ignore]
rules = ["fastapi-doctor/FASTT012", "fastapi-doctor/FASTT016"]
files = ["migrations/**", "seed.py"]

[[tool.fastapi-doctor.ignore.overrides]]
files = ["app/routers/health.py"]
rules = ["fastapi-doctor/FASTT001"]

[[tool.fastapi-doctor.ignore.overrides]]
files = ["tests/**"]
# omit 'rules' to suppress all rules for these files
```

## Rules

### Async/Sync Correctness

| Rule | Severity | Detects |
|---|---|---|
| FASTT001 | ERROR | Sync blocking IO (`requests.get`, `time.sleep`) in async endpoint |
| FASTT002 | ERROR | Sync SQLAlchemy calls in async endpoint |
| FASTT003 | WARN/ERROR | `async def` endpoint with no await |
| FASTT004 | ERROR | `asyncio.run()` inside async context — nested event loop |
| FASTT005 | ERROR | `open()` blocking file I/O in async endpoint |
| FASTT006 | WARNING | `subprocess.run()` / `os.system()` in async endpoint |

### Security & Data Leaks

| Rule | Severity | Detects |
|---|---|---|
| FASTT010 | ERROR | ORM model returned directly (data leakage) |
| FASTT011 | ERROR | `response_model=None` with sensitive data |
| FASTT012 | WARNING | GET endpoint missing `response_model` |
| FASTT013 | ERROR/WARN | Hardcoded secrets: API keys, tokens, passwords |
| FASTT014 | WARNING | `debug=True` in production (FastAPI + uvicorn) |
| FASTT015 | ERROR | CORS wildcard origins with credentials |
| FASTT016 | WARNING | Missing `HTTPSRedirectMiddleware` |
| FASTT017 | ERROR | SQL f-string injection |

### HTTP Correctness

| Rule | Severity | Detects |
|---|---|---|
| FASTT070 | WARNING | POST/PUT/PATCH/DELETE missing explicit `status_code` |

## Agent Installer

```bash
# Install skill for all detected AI agents
fastapi-therapist install

# Non-interactive mode
fastapi-therapist install --yes

# Preview without writing files
fastapi-therapist install --dry-run
```

## Score

The health score formula:

```
100 - (unique error rules × 1.5) - (unique warning rules × 0.75)
```

- **75–100** Great
- **50–74** Needs work
- **0–49** Critical
