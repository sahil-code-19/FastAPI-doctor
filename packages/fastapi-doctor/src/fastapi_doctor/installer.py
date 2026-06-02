import sys
import shutil
import os

from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Agent:
    name: str
    binary: str
    config_dir: str
    skill_path_template: str
    skill_format: str


KNOWN_AGENTS = [
    Agent(
        name="OpenCode",
        binary="opencode",
        config_dir="",
        skill_path_template=".opencode/skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    ),
    Agent(
        name="Claude Code",
        binary="claude",
        config_dir=".claude",
        skill_path_template="skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    ),
    Agent(
        name="Cursor",
        binary="cursor",
        config_dir="",
        skill_path_template=".cursor/rules/fastapi-therapist.md",
        skill_format="markdown",
    ),
    Agent(
        name="Codex",
        binary="codex",
        config_dir=".codex",
        skill_path_template="skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    ),
    Agent(
        name="Gemini CLI",
        binary="gemini",
        config_dir=".gemini",
        skill_path_template="skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    ),
    Agent(
        name="GitHub Copilot",
        binary="copilot",
        config_dir="",
        skill_path_template=".copilot/skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    ),
]

SKILL_CONTENT = """---
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
"""


def detect_agents() -> list[Agent]:
    """Detect installed AI agents via PATH and filesystem checks."""
    detected: list[Agent] = []

    for agent in KNOWN_AGENTS:
        found = False

        if shutil.which(agent.binary):
            found = True

        home = Path.home()
        if agent.config_dir:
            config_path = home / agent.config_dir
            if config_path.exists() and config_path.is_dir():
                found = True

        if found:
            detected.append(agent)
    return detected


def install_skill(
    agent: Agent, project_root: Path | None = None, dry_run: bool = False
):
    """Write SKILL.md to the agent's config directory."""
    if project_root is None:
        project_root = Path.cwd()

    skill_path = project_root / agent.skill_path_template

    if dry_run:
        return f"[DRY RUN] {agent.name}: {skill_path}"

    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(SKILL_CONTENT, encoding="utf-8")
    return f"{agent.name}: {skill_path}"


def run_install(yes: bool = False, dry_run: bool = False, cwd: Path | None = None):
    """Main install entry point — detect agents and install skill."""
    if cwd is None:
        cwd = Path.cwd()

    detected = detect_agents()

    if not detected:
        print("No AI agents detected on this system.", file=sys.stderr)
        print("Searched:", file=sys.stderr)
        for agent in KNOWN_AGENTS:
            print(
                f"  - {agent.name} (binary: {agent.binary}, config: ~/{agent.config_dir})",
                file=sys.stderr,
            )
        sys.exit(0)

    if not yes and not dry_run:
        print("Detected agents:")
        for i, agent in enumerate(detected):
            print(f"  [{i + 1}] {agent.name}")

        response = (
            input(f"\nInstall skill to all {len(detected)} agents? [Y/n] ")
            .strip()
            .lower()
        )
        if response and response != "y":
            print("Install cancelled.")
            return

    for agent in detected:
        result = install_skill(agent, cwd, dry_run=dry_run)
        print(result)

    if dry_run:
        print(f"\nDry run complete. {len(detected)} agents would receive the skill.")
    else:
        print(f"\nDone! Skill installed for {len(detected)} agents.")
