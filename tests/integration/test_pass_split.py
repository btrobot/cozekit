"""P2-2: Verify SemanticPass facade == FrontendPass + BackendPass."""
import glob
import os
import pytest
from tests.conftest import compile_text
from cozekit.passes.semantic_pass import SemanticPass
from cozekit.passes.frontend_pass import FrontendPass
from cozekit.passes.backend_pass import BackendPass


# Find temp YAML fixtures relative to cozekit root
_YAML_FIXTURES_DIR = '/home/dev/coze-studio/temp'
_YAML_FIXTURES = sorted(glob.glob(os.path.join(_YAML_FIXTURES_DIR, '*.yaml')))[:10]


def _run_passes(yaml_text: str, passes: list) -> list[str]:
    """Run specified passes on YAML text and return sorted rule IDs."""
    from cozekit.transport.normalizer import TransportNormalizer, InputSource
    from cozekit.passes.context import PassContext
    from cozekit.ast.builder import ASTBuilder
    from cozekit.ast.analysis_graph import AnalysisGraphBuilder
    from cozekit.sema.symbol_table import SymbolTable
    from cozekit.sema.query_authority import WorkflowSemaQueryAuthority
    from cozekit.sema.reference_resolution import resolve_all_refs

    norm = TransportNormalizer()
    source = InputSource(text=yaml_text, path=None)
    doc = norm.normalize(source)
    ast_builder = ASTBuilder()
    wf_ast = ast_builder.build(doc)

    version_is_valid = isinstance(doc.versions, dict) if doc.versions is not None else None
    flat, indices = AnalysisGraphBuilder().build(
        wf_ast, versions=doc.versions, version_is_valid=version_is_valid, envelope_type=doc.envelope_type,
    )
    symtab = SymbolTable(flat, indices)
    resolution_table = resolve_all_refs(flat, symtab)
    sema = WorkflowSemaQueryAuthority(symtab, resolution_table)

    ctx = PassContext(
        sema=sema, source_text=doc.source_text, source_file=doc.source_file,
        transport_format=doc.transport_format, span_map=doc.span_map,
    )

    diags = []
    for p in passes:
        diags.extend(p.run(ctx))
    return sorted(d.rule_id for d in diags)


class TestPassNames:
    def test_frontend_pass_name(self):
        assert FrontendPass().name == 'semantic-fe'

    def test_backend_pass_name(self):
        assert BackendPass().name == 'semantic-be'

    def test_facade_name(self):
        assert SemanticPass().name == 'semantic'


class TestFacadeVsSplit:
    """SemanticPass facade output == FrontendPass + BackendPass output."""

    def test_valid_yaml_equivalence(self):
        yaml = """
nodes:
  - id: "100001"
    type: "1"
    data:
      nodeMeta:
        title: Start
  - id: "900001"
    type: "2"
    data:
      nodeMeta:
        title: End
edges:
  - sourceNodeID: "100001"
    targetNodeID: "900001"
"""
        facade = _run_passes(yaml, [SemanticPass()])
        split = _run_passes(yaml, [FrontendPass(), BackendPass()])
        assert facade == split, f"Facade: {facade}\nSplit:   {split}"


@pytest.mark.parametrize("yaml_path", _YAML_FIXTURES, ids=lambda p: os.path.basename(p))
def test_yaml_fixture_equivalence(yaml_path):
    """Real YAML fixture: facade diagnostics == split diagnostics."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        text = f.read()
    facade = _run_passes(text, [SemanticPass()])
    split = _run_passes(text, [FrontendPass(), BackendPass()])
    assert facade == split, (
        f"Mismatch in {os.path.basename(yaml_path)}\n"
        f"Facade: {facade}\nSplit:   {split}"
    )
