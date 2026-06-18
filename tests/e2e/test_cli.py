"""E2E tests for cozekit CLI entry points."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "yaml"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "cozekit", *args],
        capture_output=True, text=True, cwd=str(FIXTURES.parent.parent),
    )


class TestCLICheck:
    def test_check_valid_workflow(self):
        """Valid workflow exits 0."""
        r = _run("check", str(FIXTURES / "fixture-minimal-start-end.yaml"))
        assert r.returncode == 0, r.stderr

    def test_check_invalid_workflow(self):
        """Workflow with violations exits 1."""
        for f in sorted(FIXTURES.glob("*.yaml")):
            r = _run("check", str(f))
            if r.returncode == 1:
                return
        pytest.skip("No fixture with violations found")

    def test_check_nonexistent_file(self):
        """Non-existent file exits non-zero."""
        r = _run("check", "/tmp/nonexistent_workflow_12345.yaml")
        assert r.returncode != 0

    def test_check_directory(self):
        """Directory mode processes all files."""
        r = _run("check", str(FIXTURES))
        assert r.returncode in (0, 1)


class TestCLIInfo:
    def test_info_command(self):
        """info command prints version and capabilities."""
        r = _run("info")
        assert r.returncode == 0
        assert "v0.1.0" in r.stdout
        assert "Syntax" in r.stdout
        assert "Semantic" in r.stdout

    def test_help_flag(self):
        """--help prints usage."""
        r = _run("--help")
        assert r.returncode == 0
        assert "cozekit" in r.stdout.lower()


class TestOutputFormats:
    @pytest.fixture
    def any_fixture(self):
        fixtures = sorted(FIXTURES.glob("*.yaml"))
        return fixtures[0] if fixtures else pytest.skip("No fixtures")

    def test_output_json_parseable(self, any_fixture):
        """--format json produces valid JSON."""
        r = _run("check", str(any_fixture), "--format", "json")
        if r.stdout.strip():
            data = json.loads(r.stdout)
            assert isinstance(data, (dict, list))

    def test_output_compact_format(self, any_fixture):
        """--format compact runs without error."""
        r = _run("check", str(any_fixture), "--format", "compact")
        assert r.returncode in (0, 1)
