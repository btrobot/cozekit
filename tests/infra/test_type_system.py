"""Tests for P3 type system: ParameterTypeFact, resolve_ref_type, build_parameter_type_facts."""

from __future__ import annotations

import unittest

from cozekit.ast.workflow_ast import (
    ParameterAST, RefAST, NodeAST, CanvasAST, EdgeAST,
)
from cozekit.ast.analysis_graph import AnalysisGraph
from cozekit.ast.indices import ASTIndices, build_ast_indices
from cozekit.sema.symbol_table import SymbolTable
from cozekit.sema.type_system import (
    TypeFact, TypeCategory, CompatibilityState,
    canonicalize_type, infer_type, check_compatibility,
    ParameterTypeFact, resolve_ref_type, build_parameter_type_facts,
    extract_declared_type_from_param,
)


def _make_flat(*nodes: NodeAST, edges: tuple[EdgeAST, ...] = ()) -> tuple[AnalysisGraph, ASTIndices]:
    """Build a minimal AnalysisGraph + ASTIndices from nodes."""
    canvas = CanvasAST(
        canvas_id='root',
        canvas_path=(),
    )
    flat = AnalysisGraph(
        root_canvas_path=(),
        nodes=nodes,
        edges=edges,
        canvases=(canvas,),
    )
    indices = build_ast_indices(flat)
    return flat, indices


class TestResolveRefType(unittest.TestCase):
    """S1: resolve_ref_type tests."""

    def _build_symtab(self, *nodes: NodeAST) -> SymbolTable:
        flat, indices = _make_flat(*nodes)
        return SymbolTable(flat, indices)

    def test_resolves_target_declared_type(self) -> None:
        """T1.1: resolve_ref_type returns target's declared type."""
        source = NodeAST(
            node_id='source-1', node_type='20',
            parameters=(
                ParameterAST(name='result', left_type='integer'),
            ),
        )
        consumer = NodeAST(
            node_id='consumer-1', node_type='20',
            parameters=(
                ParameterAST(
                    name='input',
                    left_type='string',
                    input_ref=RefAST(ref_type='ref', block_id='source-1', name='result'),
                ),
            ),
        )
        symtab = self._build_symtab(source, consumer)
        ref = consumer.parameters[0].input_ref
        assert ref is not None
        result = resolve_ref_type(ref, symbol_table=symtab)
        self.assertEqual(result, 'integer')

    def test_returns_none_for_missing_target(self) -> None:
        """T1.2: resolve_ref_type returns None for nonexistent block_id."""
        consumer = NodeAST(
            node_id='consumer-1', node_type='20',
            parameters=(
                ParameterAST(
                    name='input',
                    input_ref=RefAST(ref_type='ref', block_id='nonexistent', name='field'),
                ),
            ),
        )
        symtab = self._build_symtab(consumer)
        ref = consumer.parameters[0].input_ref
        assert ref is not None
        result = resolve_ref_type(ref, symbol_table=symtab)
        self.assertIsNone(result)

    def test_returns_none_for_undeclared_type(self) -> None:
        """T1.3: resolve_ref_type returns None when target has no declared type."""
        source = NodeAST(
            node_id='source-1', node_type='20',
            parameters=(
                ParameterAST(name='result'),  # no left_type
            ),
        )
        consumer = NodeAST(
            node_id='consumer-1', node_type='20',
            parameters=(
                ParameterAST(
                    name='input',
                    input_ref=RefAST(ref_type='ref', block_id='source-1', name='result'),
                ),
            ),
        )
        symtab = self._build_symtab(source, consumer)
        ref = consumer.parameters[0].input_ref
        assert ref is not None
        result = resolve_ref_type(ref, symbol_table=symtab)
        self.assertIsNone(result)


class TestBuildParameterTypeFacts(unittest.TestCase):
    """S1: build_parameter_type_facts tests."""

    def _build_symtab(self, *nodes: NodeAST) -> SymbolTable:
        flat, indices = _make_flat(*nodes)
        return SymbolTable(flat, indices)

    def test_captures_compatible_types(self) -> None:
        """T1.4a: matching types -> COMPATIBLE."""
        source = NodeAST(
            node_id='src', node_type='20',
            parameters=(ParameterAST(name='out', left_type='string'),),
        )
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(
                    name='in', left_type='string',
                    input_ref=RefAST(ref_type='ref', block_id='src', name='out'),
                ),
            ),
        )
        symtab = self._build_symtab(source, consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertEqual(fact.declared_type, 'string')
        self.assertEqual(fact.ref_target_type, 'string')
        self.assertEqual(fact.compatibility, CompatibilityState.COMPATIBLE)

    def test_detects_incompatible_types(self) -> None:
        """T1.4b: mismatched types -> INCOMPATIBLE."""
        source = NodeAST(
            node_id='src', node_type='20',
            parameters=(ParameterAST(name='out', left_type='integer'),),
        )
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(
                    name='in', left_type='string',
                    input_ref=RefAST(ref_type='ref', block_id='src', name='out'),
                ),
            ),
        )
        symtab = self._build_symtab(source, consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertEqual(fact.compatibility, CompatibilityState.INCOMPATIBLE)

    def test_global_var_ref_runtime_deferred(self) -> None:
        """T1.4c: global variable ref -> RUNTIME_DEFERRED."""
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(
                    name='in', left_type='string',
                    input_ref=RefAST(ref_type='ref', source='global_variable_app', name='my_var'),
                ),
            ),
        )
        symtab = self._build_symtab(consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertEqual(fact.compatibility, CompatibilityState.RUNTIME_DEFERRED)

    def test_no_ref_unknown(self) -> None:
        """T1.4d: no ref -> UNKNOWN."""
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(name='in', left_type='string'),
            ),
        )
        symtab = self._build_symtab(consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertEqual(fact.compatibility, CompatibilityState.UNKNOWN)

    def test_declared_type_canonicalized(self) -> None:
        """T1.4e: declared type is canonicalized (e.g. 'str' -> 'string')."""
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(name='in', left_type='str'),
            ),
        )
        symtab = self._build_symtab(consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertEqual(fact.declared_type, 'string')

    def test_meta_type_filtered(self) -> None:
        """T1.4f: meta-types like 'ref' are filtered out."""
        consumer = NodeAST(
            node_id='cons', node_type='20',
            parameters=(
                ParameterAST(name='in', left_type='ref'),
            ),
        )
        symtab = self._build_symtab(consumer)
        fact = build_parameter_type_facts(consumer.parameters[0], symbol_table=symtab)
        self.assertIsNone(fact.declared_type)
