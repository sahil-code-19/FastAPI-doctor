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

# Only scan changed files (git diff vs base branch)
fastapi-therapist . --diff

# Only scan staged files (pre-commit hook)
fastapi-therapist . --staged

# Output only the score (useful for CI)
fastapi-therapist . --score

# Audit mode — ignore inline suppressions, reveal hidden issues
fastapi-therapist . --audit

# CI: GitHub Actions annotations inline on PR diff
fastapi-therapist . --annotations

# CI: machine-readable JSON output
fastapi-therapist . --json

# Include ruff linting results
fastapi-therapist . --ruff

# Include dead code detection
fastapi-therapist . --vulture

# Install skill for AI coding agents
fastapi-therapist install
```

## Configuration

Suppress rules or skip files via `pyproject.toml` or `fastapi-doctor.config.json`:

```toml
[tool.fastapi-doctor]
ruff = true           # always include ruff
failOn = "warning"    # strict CI gate

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

## Inline Suppression

```python
@app.post("/items")  # fastapi-doctor-disable-line FASTT070

# fastapi-doctor-disable-next-line FASTT002
@router.put("/items/{id}")
async def update_item(...):
    ...

return user  # fastapi-doctor-disable-line (all rules)
```

## File Ignores

Respects existing project ignore files automatically:

| Source | Example |
|---|---|
| `.gitignore` | `*.pyc`, `secrets.py` |
| `ruff.toml` / `.ruff.toml` | `exclude = ["migrations/*"]` |
| `pyproject.toml` (`[tool.ruff]`) | `exclude = ["generated/*"]` |
| `.gitattributes` | `vendor/** linguist-vendored` |

## Rules

### Async/Sync Correctness

| Rule | Severity | Detects |
|---|---|---|
| FASTT001 | ERROR | Sync blocking IO in async endpoint |
| FASTT002 | ERROR | Sync SQLAlchemy calls in async endpoint |
| FASTT003 | WARN/ERROR | `async def` endpoint with no await |
| FASTT004 | ERROR | `asyncio.run()` — nested event loop |
| FASTT005 | ERROR | `open()` blocking file I/O |
| FASTT006 | WARNING | `subprocess.run()` / `os.system()` |

### Security & Data Leaks

| Rule | Severity | Detects |
|---|---|---|
| FASTT010 | ERROR | ORM model returned directly |
| FASTT011 | ERROR | `response_model=None` with sensitive data |
| FASTT012 | WARNING | GET endpoint missing `response_model` |
| FASTT013 | ERROR/WARN | Hardcoded secrets |
| FASTT014 | WARNING | `debug=True` in production |
| FASTT015 | ERROR | CORS wildcard origins with credentials |
| FASTT016 | WARNING | Missing `HTTPSRedirectMiddleware` |
| FASTT017 | ERROR | SQL f-string injection |

### Architecture

| Rule | Severity | Detects |
|---|---|---|
| FASTT020 | ERROR | `Depends()` inside function body |
| FASTT021 | WARNING | Global mutable state in handler |
| FASTT022 | WARNING | God file (no `APIRouter` separation) |
| FASTT024 | WARNING | Raw `connect()` in startup |
| FASTT025 | WARNING | Deprecated `@app.on_event()` |
| FASTT026 | WARNING | Unused `request: Request` parameter |
| FASTT027 | WARNING | `File()` instead of `UploadFile` |

### Performance

| Rule | Severity | Detects |
|---|---|---|
| FASTT030 | ERROR | N+1 query pattern |
| FASTT031 | WARNING | Unindexed `ForeignKey` |
| FASTT033 | WARNING | CPU-bound work in async without `to_thread` |
| FASTT034 | WARNING | `BackgroundTasks` wrapping Celery |
| FASTT035 | ERROR | Unbounded query (`.all()` without pagination) |
| FASTT036 | WARNING | Missing `@lru_cache` on `get_settings()` |

### Pydantic Usage

| Rule | Severity | Detects |
|---|---|---|
| FASTT040 | WARNING | Pydantic v1 `@validator` in v2 project |
| FASTT041 | WARNING | `orm_mode = True` never used |
| FASTT042 | WARNING | `dict(model)` instead of `model_dump()` |
| FASTT043 | ERROR | Raw `dict` return with `response_model` set |
| FASTT044 | WARNING | Missing `from_attributes=True` |

### Dependency Injection

| Rule | Severity | Detects |
|---|---|---|
| FASTT050 | ERROR | `yield` without `try/finally` |
| FASTT051 | WARNING | `Depends` repeated across routes |
| FASTT052 | WARNING | `Session()` return instead of `yield` |
| FASTT053 | WARNING | Auth at route level, not router level |

### Dead Code (via vulture)

| Rule | Severity | Detects |
|---|---|---|
| FASTT060 | WARNING | Unused class/schema |
| FASTT061 | WARNING | Unused function |
| FASTT063 | WARNING | Unused import/variable |

Enable with `--vulture` or `vulture = true` in config.

### HTTP Correctness

| Rule | Severity | Detects |
|---|---|---|
| FASTT070 | WARNING | POST/PUT/PATCH/DELETE missing `status_code` |

## Agent Installer

```bash
fastapi-therapist install         # interactive
fastapi-therapist install --yes   # non-interactive
fastapi-therapist install --dry-run  # preview
```

## Score

```
100 - (unique error rules × 1.5) - (unique warning rules × 0.75)
```

- **75–100** Great
- **50–74** Needs work
- **0–49** Critical
