How to Run Against Your FastAPI Project

1. First clone the repo.
2. Go the project root and run command `uv sync`
3. run the following commands at the project root:
```
python -m fastapi_doctor.cli fastapi_project_path_that_you_want_scan

- Full scan
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project
- With file locations
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project --verbose
- Score only
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project --score
```

SKILL.md

```
---
name: fastapi-therapist
description: Use when finishing a feature, fixing a bug, before committing FastAPI code.
version: "1.0.0"
---

# FastAPI Therapist

Scans FastAPI codebases for security, performance, correctness, and architecture issues. Outputs a 0–100 health score.

## Setup

```bash
pip install fastapi-therapist
```

## After making FastAPI code changes:

Run `fastapi-therapist . --verbose` and check the score did not regress.

If the score dropped, fix the regressions before committing.

## For general cleanup or code improvement:

Run `fastapi-therapist . --verbose` to scan the full codebase. Fix issues by severity — errors first, then warnings.

## Command

```bash
fastapi-therapist . --verbose
```

| Flag        | Purpose                                       |
| ----------- | --------------------------------------------- |
| `.`         | Scan current directory                        |
| `--verbose` | Show affected files and line numbers per rule |
| `--score`   | Output only the numeric score                 |

```
