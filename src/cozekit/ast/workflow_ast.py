"""Pure syntax-preserving AST — no semantic markers.

The AST preserves structural information from the YAML/JSON payload:
node identities, edge connections, parameter structures, and source provenance.
Semantic interpretation (types, scopes, references) belongs to the sema layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..diagnostics.core import SourceSpan


@dataclass(frozen=True)
class SourceProvenance:
    """Source location for an AST node."""
    source_file: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class RefAST:
    """Syntax-preserving parameter reference payload."""
    ref_type: str | None = None
    source: str | None = None
    block_id: str | None = None
    name: str | None = None
    path: tuple[str, ...] = ()
    provenance: SourceProvenance = field(default_factory=SourceProvenance)


@dataclass(frozen=True)
class ParameterAST:
    """Syntax-preserving node input parameter."""
    name: str | None = None
    left_type: str | None = None
    input_ref: RefAST | None = None
    left_ref: RefAST | None = None
    right_ref: RefAST | None = None
    provenance: SourceProvenance = field(default_factory=SourceProvenance)


@dataclass(frozen=True)
class ConditionBranchAST:
    """Single condition expression within a branch."""
    left: ParameterAST | None = None
    operator: str | None = None
    right: ParameterAST | None = None


@dataclass(frozen=True)
class ConditionAST:
    """Condition expression — list of condition branches."""
    branches: tuple[ConditionBranchAST, ...] = ()


@dataclass(frozen=True)
class BranchAST:
    """Syntax-preserving branch representation."""
    branch_key: str | None = None
    condition: ConditionAST | None = None
    provenance: SourceProvenance = field(default_factory=SourceProvenance)


@dataclass(frozen=True)
class NodeAST:
    """Syntax-preserving node representation.

    All structural data from the YAML node is extracted into typed fields
    during AST construction. No raw dict passthrough.
    """
    node_id: str | None = None
    node_type: str | None = None
    title: str | None = None
    parameters: tuple[ParameterAST, ...] = ()
    variable_parameters: tuple[ParameterAST, ...] = ()
    branches: tuple[BranchAST, ...] = ()
    blocks: tuple[NodeAST, ...] = ()
    nested_edges: tuple[EdgeAST, ...] = ()
    has_blocks_key: bool = False
    composite_kind: str | None = None
    _has_shape_issue: bool = False
    has_data: bool = True
    is_valid_object: bool = True
    global_var_name: str | None = None
    global_var_type: str | None = None
    global_var_schema: dict | None = None
    global_var_item_type: str | None = None
    canvas_path: tuple[str | int, ...] = field(default_factory=tuple)
    non_object_node_count: int = 0
    provenance: SourceProvenance = field(default_factory=SourceProvenance)
    on_error_config: dict | None = None
    source_span: SourceSpan | None = None
    # Node-specific parameters (e.g., llmParam for LLM nodes)
    node_specific_params: tuple[ParameterAST, ...] = ()
    outputs: tuple[OutputVarAST, ...] = ()


@dataclass(frozen=True)
class EdgeAST:
    """Syntax-preserving edge representation."""
    source_node_id: str | None = None
    target_node_id: str | None = None
    source_port_id: str | None = None
    target_port_id: str | None = None
    canvas_path: tuple[str | int, ...] = field(default_factory=tuple)
    non_object_node_count: int = 0
    provenance: SourceProvenance = field(default_factory=SourceProvenance)
    on_error_config: dict | None = None
    source_span: SourceSpan | None = None


@dataclass(frozen=True)
class CanvasAST:
    """Syntax-preserving canvas representation."""
    canvas_id: str | None = None
    nodes: tuple[NodeAST, ...] = ()
    edges: tuple[EdgeAST, ...] = ()
    parameters: tuple[ParameterAST, ...] = ()
    canvas_path: tuple[str | int, ...] = field(default_factory=tuple)
    non_object_node_count: int = 0
    provenance: SourceProvenance = field(default_factory=SourceProvenance)
    # Structural metadata fields (not semantic)
    owner_node_type: str | None = None
    owner_node_id: str | None = None
    parent_canvas_path: tuple[str | int, ...] | None = None
    raw_node_count: int = 0
    shape_is_valid: bool = True
    nested_shape_issues: int = 0
    shape_issues: frozenset[str] = frozenset()


@dataclass(frozen=True)
class WorkflowAST:
    """Top-level workflow AST — pure syntax, no semantics."""
    root_canvas: CanvasAST = field(default_factory=CanvasAST)
    canvases: tuple[CanvasAST, ...] = ()
    provenance: SourceProvenance = field(default_factory=SourceProvenance)


@dataclass(frozen=True)
class OutputVarAST:
    """Single output variable definition (tree node)."""
    name: str | None = None
    var_type: str | None = None
    required: bool = False
    default_value: str | None = None
    children: tuple[OutputVarAST, ...] = ()
    source_span: SourceSpan | None = None
