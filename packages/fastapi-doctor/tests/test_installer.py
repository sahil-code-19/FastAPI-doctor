"""Test agent detection and skill installation."""

import sys
from pathlib import Path
from io import StringIO

from fastapi_doctor.installer import (
    Agent,
    KNOWN_AGENTS,
    SKILL_CONTENT,
    detect_agents,
    install_skill,
    run_install,
)


def test_detect_agents_uses_known_agent_list():
    agents = detect_agents()
    assert isinstance(agents, list)
    # Returns subset of KNOWN_AGENTS (may be empty in CI)
    for agent in agents:
        assert isinstance(agent, Agent)
        assert agent.name in {a.name for a in KNOWN_AGENTS}


def test_install_skill_writes_file(tmp_path):
    agent = Agent(
        name="TestAgent",
        binary="fake-agent",
        config_dir="",
        skill_path_template=".testagent/skills/fastapi-therapist/SKILL.md",
        skill_format="markdown",
    )

    result = install_skill(agent, project_root=tmp_path)
    expected_path = tmp_path / ".testagent/skills/fastapi-therapist/SKILL.md"

    assert expected_path.exists()
    assert "fastapi-therapist" in expected_path.read_text()
    assert agent.name in result
    assert str(expected_path) in result


def test_install_skill_dry_run_does_not_write(tmp_path):
    agent = Agent(
        name="TestAgent",
        binary="fake-agent",
        config_dir="",
        skill_path_template=".testagent/SKILL.md",
        skill_format="markdown",
    )

    result = install_skill(agent, project_root=tmp_path, dry_run=True)
    expected_path = tmp_path / ".testagent/SKILL.md"

    assert not expected_path.exists()
    assert "[DRY RUN]" in result


def test_install_skill_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    agent = Agent(
        name="TestAgent",
        binary="fake-agent",
        config_dir="",
        skill_path_template=".testagent/SKILL.md",
        skill_format="markdown",
    )

    result = install_skill(agent)
    expected_path = tmp_path / ".testagent/SKILL.md"
    assert expected_path.exists()


def test_run_install_no_agents_shows_help(monkeypatch):
    stderr_io = StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_io)

    import fastapi_doctor.installer as installer

    monkeypatch.setattr(installer, "detect_agents", lambda: [])

    import pytest

    with pytest.raises(SystemExit) as exc:
        run_install(yes=True)
    assert exc.value.code == 0
    assert "No AI agents detected" in stderr_io.getvalue()


def test_run_install_dry_run_output(tmp_path, monkeypatch):
    import fastapi_doctor.installer as installer

    test_agent = Agent(
        name="TestAgent",
        binary="fake-agent",
        config_dir="",
        skill_path_template=".testagent/SKILL.md",
        skill_format="markdown",
    )
    monkeypatch.setattr(installer, "detect_agents", lambda: [test_agent])

    run_install(yes=True, dry_run=True, cwd=tmp_path)

    expected_path = tmp_path / ".testagent/SKILL.md"
    assert not expected_path.exists()


def test_run_install_yes_writes_files(tmp_path, monkeypatch):
    stderr_io = StringIO()
    monkeypatch.setattr(sys, "stderr", stderr_io)

    import fastapi_doctor.installer as installer

    test_agent = Agent(
        name="TestAgent",
        binary="fake-agent",
        config_dir="",
        skill_path_template=".testagent/SKILL.md",
        skill_format="markdown",
    )
    monkeypatch.setattr(installer, "detect_agents", lambda: [test_agent])

    run_install(yes=True, cwd=tmp_path)

    expected_path = tmp_path / ".testagent/SKILL.md"
    assert expected_path.exists()
    assert expected_path.read_text() == SKILL_CONTENT


def test_known_agents_have_valid_fields():
    for agent in KNOWN_AGENTS:
        assert agent.name
        assert agent.binary
        assert agent.skill_path_template
        assert agent.skill_format
        assert isinstance(agent.name, str)
        assert isinstance(agent.binary, str)


def test_skill_content_is_valid_markdown():
    assert "---" in SKILL_CONTENT
    assert "name: fastapi-therapist" in SKILL_CONTENT
    assert "fastapi-therapist . --verbose" in SKILL_CONTENT
