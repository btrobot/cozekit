"""Gate tests: engineering health guardrails."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.gate

FIXTURES_YAML = Path(__file__).resolve().parent.parent / "fixtures" / "yaml"


class TestGateCounts:
    def test_pass_count(self):
        """Pipeline must have >= 3 registered passes."""
        from cozekit.api import _get_pipeline
        pipeline = _get_pipeline()
        count = len(pipeline.pass_registry._passes)
        assert count >= 3, f"Only {count} passes, expected >= 3"

    def test_yaml_fixture_count(self):
        """YAML fixtures must be >= 8 to maintain coverage."""
        fixtures = list(FIXTURES_YAML.glob("*.yaml"))
        assert len(fixtures) >= 8, f"Only {len(fixtures)} YAML fixtures, expected >= 8"

    def test_test_file_count(self):
        """Test files must be >= 95 to maintain coverage."""
        test_files = list(Path(__file__).resolve().parent.parent.rglob("test_*.py"))
        assert len(test_files) >= 95, f"Only {len(test_files)} test files, expected >= 95"


class TestGatePerformance:
    def test_all_fixtures_under_5s(self):
        """All YAML fixtures must compile within 5 seconds total."""
        from cozekit.api import compile_path
        fixtures = sorted(FIXTURES_YAML.glob("*.yaml"))
        if not fixtures:
            pytest.skip("No YAML fixtures")

        start = time.monotonic()
        for f in fixtures:
            try:
                compile_path(f)
            except Exception:
                pass
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"All fixtures took {elapsed:.1f}s, expected < 5.0s"


class TestGateStability:
    def test_no_panic_on_fixtures(self):
        """No fixture may cause an unhandled exception."""
        from cozekit.api import compile_path
        errors = []
        for f in sorted(FIXTURES_YAML.glob("*.yaml")):
            try:
                compile_path(f)
            except Exception as e:
                errors.append((f.name, str(e)))
        assert not errors, f"Panics on fixtures: {errors}"
