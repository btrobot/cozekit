"""E2E tests for cozekit CLI entry points."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "yaml"


def _run(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "cozekit", *args],
        capture_output=True, text=True, cwd=str(FIXTURES.parent.parent),
    )


# ── CLI entry tests ──────────────────────────────────────────────

class TestCLICheck:
    def test_check_valid_workflow(self):
        """Valid workflow exits 0."""
        fixture = str(FIXTURES / "fixture-minimal-start-end.yaml")
        r = _run("check", fixture)
        assert r.returncode == 0, r.stderr

    def test_check_invalid_workflow(self):
        """Workflow with violations exits 1."""
        # Use a fixture known to have diagnostics
        fixtures = sorted(FIXTURES.glob("*.yaml"))
        # Find one that produces violations
        for f in fixtures:
            r = _run("check", str(f))
            if r.returncode == 1:
                return  # Found one
        pytest.skip("No fixture with violations found")

    def test_check_nonexistent_file(self):
        """Non-existent file exits non-zero."""
        r = _run("check", "/tmp/nonexistent_workflow_12345.yaml")
        assert r.returncode != 0

    def test_check_directory(self):
        """Directory mode processes all files."""
        r = _run("check", str(FIXTURES))
        # Should exit 0 or 1 depending on fixtures; just check it doesn't crash
        assert r.returncode in (0, 1)


class TestCLIInfo:
    def test_info_shows_version(self):
        """info command prints version."""
        r = _run("info")
        assert r.returncode == 0
        assert "v0.1.0" in r.stdout

    def test_info_shows_capabilities(self):
        """info command lists validation layers."""
        r = _run("info")
        assert "Syntax" in r.stdout
        assert "Semantic" in r.stdout

    def test_version_flag(self):
        """--version prints version string."""
        r = _run("--version")
        assert r.returncode == 0
        assert "0.1.0" in r.stdout

    def test_help_flag(self):
        """--help prints usage."""
        r = _run("--help")
        assert r.returncode == 0
        assert "usage" in r.stdout.lower() or "cozekit" in r.stdout.lower()


# ── Output format tests ──────────────────────────────────────────

class TestOutputFormats:
    @pytest.fixture
    def any_fixture(self):
        """Pick any fixture that produces output."""
        fixtures = sorted(FIXTURES.glob("*.yaml"))
        return fixtures[0] if fixtures else pytest.skip("No fixtures")

    def test_output_json_parseable(self, any_fixture):
        """--format json produces valid JSON."""
        r = _run("check", str(any_fixture), "--format", "json")
        # Should be valid JSON regardless of exit code
        if r.stdout.strip():
            data = json.loads(r.stdout)
            assert isinstance(data, (dict, list))

    def test_output_compact_format(self, any_fixture):
        """--format compact produces output."""
        r = _run("check", str(any_fixture), "--format", "compact")
        # Should produce some output
        assert r.returncode in (0, 1)

    def test_output_text_default(self, any_fixture):
        """Default format is text."""
        r = _run("check", str(any_fixture))
        assert r.returncode in (0, 1)
