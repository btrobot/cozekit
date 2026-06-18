"""Shared test fixtures and helpers for all rule tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def compile_text(text: str):
    """Compile YAML text and return the report."""
    from cozekit.api import compile_text
    return compile_text(text)


def compile_fixture(fixture_path):
    """Compile a fixture file and return the report."""
    from cozekit.api import compile_path
    return compile_path(fixture_path)


def rule_ids(report, prefix: str) -> list[str]:
    """Extract rule IDs matching prefix from report."""
    return sorted(d.rule_id for d in report.diagnostics if d.rule_id.startswith(prefix))


def violations(report, prefix: str) -> list[str]:
    """Extract violation rule IDs matching prefix from report."""
    return sorted(
        d.rule_id for d in report.diagnostics
        if d.rule_id.startswith(prefix) and d.kind == 'violation'
    )


# ── Minimal valid workflow YAML ──────────────────────────────────
MINIMAL_START_END = (
    'nodes:\n'
    '  - id: "100001"\n'
    '    type: "1"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "Start"\n'
    '  - id: "900001"\n'
    '    type: "2"\n'
    '    data:\n'
    '      nodeMeta:\n'
    '        title: "End"\n'
    'edges:\n'
    '  - sourceNodeID: "100001"\n'
    '    targetNodeID: "900001"\n'
)


def wrap_workflow(*nodes_yaml: str, edges: str | None = None) -> str:
    """Build a complete workflow YAML from node definitions.

    Automatically adds Start (100001) and End (900001) nodes, and
    connects them through the given nodes in order.

    Each nodes_yaml entry should be a raw YAML node block (indented 4 spaces).
    If edges is None, auto-chains: Start -> n1 -> n2 -> ... -> End.
    """
    # Build nodes list
    all_nodes = [
        '  - id: "100001"\n    type: "1"\n    data:\n      nodeMeta:\n        title: "Start"',
    ]
    node_ids = []
    for i, ny in enumerate(nodes_yaml):
        # Extract node id from the YAML
        import re
        m = re.search(r"id:\s*['\"]?(\w+)['\"]?", ny)
        nid = m.group(1) if m else f"n{i+1}"
        node_ids.append(nid)
        all_nodes.append(ny.rstrip())
    all_nodes.append(
        '  - id: "900001"\n    type: "2"\n    data:\n      nodeMeta:\n        title: "End"'
    )

    # Build edges
    if edges is None:
        chain = ["100001"] + node_ids + ["900001"]
        edge_lines = []
        for src, tgt in zip(chain, chain[1:]):
            edge_lines.append(f'  - sourceNodeID: "{src}"\n    targetNodeID: "{tgt}"')
        edges_str = '\n'.join(edge_lines)
    else:
        edges_str = edges

    nodes_str = '\n'.join(all_nodes)
    return f"nodes:\n{nodes_str}\nedges:\n{edges_str}\n"

# ── Test layer markers ───────────────────────────────────────────
LAYER_MARKERS = {"unit", "integration", "spec", "regression", "e2e", "gate"}


def pytest_configure(config):
    """Register test layer markers."""
    for name in LAYER_MARKERS:
        config.addinivalue_line("markers", f"{name}: {name} test layer")


# ── E2E / Gate fixtures ──────────────────────────────────────────
@pytest.fixture
def cli_runner():
    """Click test runner for CLI tests."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def all_yaml_fixtures():
    """All YAML fixture files."""
    return sorted(Path("tests/fixtures/yaml").glob("*.yaml"))


@pytest.fixture
def x109_fixture():
    """X109 commercial fixture path."""
    return Path("tests/fixtures/yaml/x109_commercial.yaml")

def pytest_collection_modifyitems(items):
    """Apply layer markers based on test file path."""
    for item in items:
        path = str(item.fspath)

        # Already has an explicit layer marker? Skip.
        item_markers = {m.name for m in item.iter_markers()}
        if item_markers & LAYER_MARKERS:
            continue

        # Apply markers based on path
        if '/spec/' in path:
            item.add_marker(pytest.mark.spec)
        elif '/unit/' in path:
            item.add_marker(pytest.mark.unit)
        elif '/integration/' in path:
            item.add_marker(pytest.mark.integration)
