# fastapi-therapist

Diagnose FastAPI codebases for security, performance, correctness, and architecture issues. Outputs a 0–100 health score.

## Installation

```bash
pip install fastapi-therapist
```

## Usage

```bash
# Scan current directory with verbose output
fastapi-therapist . --verbose

# Scan a specific project
fastapi-therapist /path/to/fastapi/project --verbose

# Output only the score (useful for CI)
fastapi-therapist . --score
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

### Correctness

| Rule | Severity | Detects |
|---|---|---|
| FASTT011 | WARNING | POST/PUT/PATCH/DELETE missing explicit `status_code` |

## Score

The health score formula:

```
100 - (unique error rules × 1.5) - (unique warning rules × 0.75)
```

- **75–100** Great
- **50–74** Needs work
- **0–49** Critical
