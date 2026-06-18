"""Hard architectural boundary tests for cozekit.

These tests enforce textbook compiler architecture principles.
They make violations PHYSICALLY IMPOSSIBLE or IMMEDIATELY VISIBLE.

Layer contract:
  Transport -> AST -> AnalysisGraph -> Sema -> Passes -> Report

Rules:
  1. AST must fully represent source structure (no raw_data passthrough)
  2. IR layer is removed — AnalysisGraph replaces it
  3. No raw_data in pass imports
  4. Pipeline builds AnalysisGraph exactly once
  5. AnalysisGraph builder does NOT do name resolution (single responsibility)
  6. Passes access nodes through sema, not direct graph traversal
  7. Passes never import IR builder internals
  8. No ir/ directory exists
  9. PassContext has no ir or indices fields
"""

from __future__ import annotations

import dataclasses
import re
import unittest
from pathlib import Path

# ── Paths ──

_PROJECT = Path(__file__).parent.parent.parent / 'src' / 'cozekit'
_SEMA_PKG = _PROJECT / 'sema'
_PASSES_PKG = _PROJECT / 'passes'
_PIPELINE = _PROJECT / 'pipeline.py'


def _source(rel_path: str) -> str:
    """Read source file relative to project root."""
    return (_PROJECT / rel_path).read_text(encoding='utf-8')


def _all_py_files(root: Path):
    """Yield all .py files under root, excluding __pycache__."""
    for p in sorted(root.rglob('*.py')):
        if '__pycache__' not in str(p):
            yield p


# ════════════════════════════════════════════════════════════════
# A1: AST must extract parameters (not pass raw_data through)
# ════════════════════════════════════════════════════════════════


class TestA1_ASTCompleteness(unittest.TestCase):
    """AST must fully represent source structure."""

    def test_ast_builder_extracts_input_parameters(self) -> None:
        """ASTBuilder must populate NodeAST.parameters from inputParameters."""
        from cozekit.transport.input_source import InputSource
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.ast.builder import ASTBuilder

        yaml_text = (
            'nodes:\n'
            '  - id: "n1"\n'
            '    type: "20"\n'
            '    data:\n'
            '      inputs:\n'
            '        inputParameters:\n'
            '          - name: x\n'
            '            left:\n'
            '              type: string\n'
            'edges:\n'
            '  - sourceNodeID: "n1"\n'
            '    targetNodeID: "n2"\n'
        )
        source = InputSource(text=yaml_text)
        doc = TransportNormalizer().normalize(source)
        ast = ASTBuilder().build(doc)

        node = ast.canvases[0].nodes[0]
        self.assertGreater(
            len(node.parameters), 0,
            "NodeAST.parameters must be populated — AST must extract, not pass raw_data through"
        )
        self.assertEqual(node.parameters[0].name, 'x')
        self.assertEqual(node.parameters[0].left_type, 'string')

    def test_ast_builder_extracts_refs(self) -> None:
        """ASTBuilder must populate ParameterAST.input_ref from ref content."""
        from cozekit.transport.input_source import InputSource
        from cozekit.transport.normalizer import TransportNormalizer
        from cozekit.ast.builder import ASTBuilder

        yaml_text = (
            'nodes:\n'
            '  - id: "n1"\n'
            '    type: "20"\n'
            '    data:\n'
            '      inputs:\n'
            '        inputParameters:\n'
            '          - name: x\n'
            '            left:\n'
            '              type: string\n'
            '            input:\n'
            '              value:\n'
            '                type: ref\n'
            '                content:\n'
            '                  blockID: src\n'
            '                  path: [out]\n'
            'edges:\n'
            '  - sourceNodeID: "n1"\n'
            '    targetNodeID: "n2"\n'
        )
        source = InputSource(text=yaml_text)
        doc = TransportNormalizer().normalize(source)
        ast = ASTBuilder().build(doc)

        param = ast.canvases[0].nodes[0].parameters[0]
        self.assertIsNotNone(param.input_ref, "ParameterAST must carry input_ref")
        assert param.input_ref is not None
        self.assertEqual(param.input_ref.block_id, 'src')


# ════════════════════════════════════════════════════════════════
# A2: IR layer is removed — directory must not exist
# ════════════════════════════════════════════════════════════════


class TestA2_IRRemoved(unittest.TestCase):
    """The ir/ directory must not exist after IR removal."""

    def test_ir_directory_does_not_exist(self) -> None:
        """ir/ directory must be deleted."""
        ir_dir = _PROJECT / 'ir'
        self.assertFalse(
            ir_dir.exists(),
            "ir/ directory must be removed — AnalysisGraph replaces IR"
        )


# ════════════════════════════════════════════════════════════════
# A3: No raw_data in pass imports
# ════════════════════════════════════════════════════════════════


class TestA3_NoRawDataInPasses(unittest.TestCase):
    """Passes must not access raw_data."""

    def test_passes_do_not_use_raw_data(self) -> None:
        """Passes must not reference raw_data in code."""
        violations = []
        for f in _all_py_files(_PASSES_PKG):
            if f.name == '__init__.py':
                continue
            source = f.read_text(encoding='utf-8')
            if 'raw_data' in source:
                violations.append(f.name)
        self.assertEqual(
            violations, [],
            f"Passes must not reference raw_data: {violations}"
        )
class TestA4_PipelineSingleBuild(unittest.TestCase):
    """Pipeline must build AnalysisGraph exactly once."""

    def test_pipeline_builds_analysis_graph_once(self) -> None:
        """Pipeline must call analysis_graph_builder.build() exactly once."""
        source = _source('pipeline.py')
        # Count calls to analysis_graph_builder.build
        calls = re.findall(r'(?:self\.)?analysis_graph_builder\.build\(', source)
        self.assertEqual(
            len(calls), 1,
            f"Pipeline must build AnalysisGraph once, found {len(calls)} calls to analysis_graph_builder.build()"
        )

    def test_pipeline_has_no_rebuild_pattern(self) -> None:
        """Pipeline must not rebuild AnalysisGraph from AST after sema construction."""
        source = _source('pipeline.py')
        self.assertNotIn(
            'flat2', source,
            "Pipeline must not rebuild AnalysisGraph (flat2 pattern) — single build, then resolve"
        )

    def test_pipeline_docstring_mentions_new_shape(self) -> None:
        """Pipeline docstring must mention the new pipeline shape."""
        source = _source('pipeline.py')
        self.assertIn(
            'AnalysisGraph', source,
            "Pipeline docstring must mention AnalysisGraph in the pipeline shape"
        )


# ════════════════════════════════════════════════════════════════
# A5: Passes access nodes through sema, not direct graph traversal
# ════════════════════════════════════════════════════════════════


class TestA5_PassSemaBoundary(unittest.TestCase):
    """Passes must query sema for node access, not directly scan IR/graph."""

    def test_passes_have_no_direct_ir_canvas_traversal(self) -> None:
        """Pass source must not contain 'ctx.ir.canvases' or 'ctx.flat.canvases'."""
        violations = []
        for f in _all_py_files(_PASSES_PKG):
            if f.name == '__init__.py':
                continue
            source = f.read_text(encoding='utf-8')
            if 'ctx.ir.canvases' in source or 'ctx.flat.canvases' in source:
                violations.append(f.name)
        self.assertEqual(
            violations, [],
            f"Passes must not directly traverse graph: {violations}"
        )

    def test_passes_do_not_import_ir_internals(self) -> None:
        """Passes must not import from ir. modules."""
        violations = []
        for f in _all_py_files(_PASSES_PKG):
            if f.name == '__init__.py':
                continue
            source = f.read_text(encoding='utf-8')
            lines = source.splitlines()
            for line in lines:
                code_part = line.split('#')[0]
                if re.search(r'from\s+\S+\.ir\b', code_part) or re.search(r'import\s+\S+\.ir\b', code_part):
                    violations.append(f.name)
                    break
        self.assertEqual(
            violations, [],
            f"Passes must not import IR internals: {violations}"
        )


# ════════════════════════════════════════════════════════════════
# A6: Sema layer completeness
# ════════════════════════════════════════════════════════════════


class TestA6_SemaQueries(unittest.TestCase):
    """Sema must expose the queries passes need."""

    def test_sema_exposes_canvas_nodes_query(self) -> None:
        """WorkflowSemaQueryAuthority must have a canvas_nodes() or similar method."""
        from cozekit.sema.query_authority import WorkflowSemaQueryAuthority
        methods = [m for m in dir(WorkflowSemaQueryAuthority) if not m.startswith('_')]
        # Must have some way to get nodes by canvas
        has_node_query = any(
            'node' in m and ('canvas' in m or 'scope' in m)
            for m in methods
        )
        self.assertTrue(
            has_node_query,
            f"Sema must expose node-per-canvas query. Available: {methods}"
        )

    def test_sema_exposes_parameter_queries(self) -> None:
        """Sema must have parameter_type_facts or equivalent."""
        from cozekit.sema.query_authority import WorkflowSemaQueryAuthority
        self.assertTrue(
            hasattr(WorkflowSemaQueryAuthority, 'parameter_type_facts'),
            "Sema must expose parameter_type_facts()"
        )


# ════════════════════════════════════════════════════════════════
# A7: No IR imports in sema/ or passes/
# ════════════════════════════════════════════════════════════════


class TestA7_NoIRImports(unittest.TestCase):
    """sema/ and passes/ must not import from ir/ modules."""

    def test_no_ir_imports_in_sema(self) -> None:
        """No from.*ir imports in sema/."""
        violations = []
        for f in _all_py_files(_SEMA_PKG):
            source = f.read_text(encoding='utf-8')
            lines = source.splitlines()
            for line in lines:
                code_part = line.split('#')[0]
                if re.search(r'from\s+\S+\.ir\.', code_part) or re.search(r'import\s+\S+\.ir\.', code_part):
                    violations.append(f'{f.name}: {line.strip()}')
                    break
        self.assertEqual(
            violations, [],
            f"No IR imports allowed in sema/: {violations}"
        )

    def test_no_ir_imports_in_passes(self) -> None:
        """No from.*ir imports in passes/."""
        violations = []
        for f in _all_py_files(_PASSES_PKG):
            source = f.read_text(encoding='utf-8')
            lines = source.splitlines()
            for line in lines:
                code_part = line.split('#')[0]
                if re.search(r'from\s+\S+\.ir\.', code_part) or re.search(r'import\s+\S+\.ir\.', code_part):
                    violations.append(f'{f.name}: {line.strip()}')
                    break
        self.assertEqual(
            violations, [],
            f"No IR imports allowed in passes/: {violations}"
        )


# ════════════════════════════════════════════════════════════════
# A8: No object.__setattr__ in sema/
# ════════════════════════════════════════════════════════════════


class TestA8_NoSetattrHackInSema(unittest.TestCase):
    """Sema layer must not use object.__setattr__ hacks."""

    def test_no_object_setattr_in_sema(self) -> None:
        """No object.__setattr__ in sema/."""
        violations = []
        for f in _all_py_files(_SEMA_PKG):
            source = f.read_text(encoding='utf-8')
            if 'object.__setattr__' in source:
                violations.append(f.name)
        self.assertEqual(
            violations, [],
            f"No object.__setattr__ allowed in sema/: {violations}"
        )


# ════════════════════════════════════════════════════════════════
# A9: PassContext has no ir or indices fields
# ════════════════════════════════════════════════════════════════


class TestA9_PassContextNoIR(unittest.TestCase):
    """PassContext must not have ir or indices fields."""

    def test_pass_context_has_no_ir_field(self) -> None:
        """PassContext must not expose an 'ir' attribute."""
        from cozekit.passes.context import PassContext
        field_names = {f.name for f in dataclasses.fields(PassContext)}
        self.assertNotIn('ir', field_names, "PassContext must not have an 'ir' field")
        self.assertNotIn('indices', field_names, "PassContext must not have an 'indices' field")
