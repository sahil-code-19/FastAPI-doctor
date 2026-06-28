# FastAPI-therapist

Your FastAPI codebase has a problem or coding agent writes not good enough FastAPI code. FastAPI-therapist deterministically scans codebase and find problems - acorss architecture, security, performance, dependency injection, and code health.

[Docs ->](#) <!-- not available -->

## Install

### 1. Quick start

Run this at your FastAPI project root to get an audit.

#### Installation

```bash
uv add fastapi-therapist
```

OR

```bash
pip install fastapi-therapist
```

#### Run tool

```bash
fastapi-therapist . 
```

- note: `.` for current directory 

![Demo ->](./docs/demo.gif)

### 2. Install for agents
 
Once you have an audit, install the skill so your coding agent learns from the issues and fixes them going forward.
 
```bash
fastapi-therapist install
```
 
Works with Claude Code, Cursor, Codex, and other agent-based tools.

### 3. Run in CI 

fastapi-therapist reviews every pull request and reports only the issues you changed introduced - not your existing backlog.

```
fastapi-therapist:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Checkout the python version
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install fastapi-therapist
        run: pip install fastapi-therapist

      - name: Run fastapi-therapist
        run: fastapi-therapist . --verbose --diff
```

### 4. Configure rules

You can configure which rules to run and how to run them in `pyproject.toml` or `fastapi-doctor.config.json`

[Learn more ->](#)

## What it checks
 
50 rules across 7 categories:
 
- **Architecture** — layering violations, circular imports, route/service boundary leaks
- **Security** — missing auth dependencies, unsafe CORS, secrets in code, injection-prone queries
- **Dependency Injection** — misused `Depends()`, request-scoped state leaks, missing overrides in tests
- **Database** — N+1 queries, missing indexes, session lifecycle issues (SQLModel/SQLAlchemy)
- **Performance** — blocking calls in async routes, sync I/O in async handlers, unbounded pagination
- **Validation** — Pydantic model misuse, missing response models, loose typing on inputs
- **Code Health** — dead code, unused imports, inconsistent error handling
Each finding includes a severity, the file/line, and a short explanation of why it matters.

## Contributing
 
[Issues welcome!](#) <!--unavailable-->
 
MIT-licensed