"""Graph validators — structural and connectivity checks.

These functions validate graph-level properties: node connectivity,
edge endpoints, cycles, branch ports, nested composites, etc.
"""
from __future__ import annotations

from ..diagnostics.core import Checkability, Diagnostic
from .context import PassContext
from .constants import (
    NodeType,
    START_NODE_ID,
    END_NODE_ID,
    START_NODE_TYPE_ID,
    END_NODE_TYPE_ID,
    IF_NODE_TYPE_ID,
    INTENT_NODE_TYPE_ID,
    COMMENT_NODE_TYPE_ID,
    PARAM_NAME_PATTERN,
    COMPOSITE_NODE_TYPE_IDS,
    SUBWORKFLOW_NODE_TYPE_ID,
    LOOP_NODE_TYPE_ID,
    BATCH_NODE_TYPE_ID,
)


from .diag_helper import diag_be as _diag_be


def check_isolated_nodes(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-007: isolated nodes — checks all canvases including sub-canvas."""
    for canvas in ctx.sema.canvases():
        isolated = ctx.sema.isolated_node_ids(canvas_path=canvas.canvas_path)
        for node_id in isolated:
            node = ctx.sema.node_by_id(node_id)
            if node and node.node_type == COMMENT_NODE_TYPE_ID:
                continue  # comment nodes are visual annotations, not isolated
            span = node.source_span if node else None
            diagnostics.append(_diag_be(
                'SEMANTIC-BE-007', 'warning',
                'isolated nodes may be pruned before deeper backend validation',
                source_span=span,
            ))

def check_parameter_names(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-019: parameter name syntax."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            for param in node.parameters:
                if param.name and not PARAM_NAME_PATTERN.match(param.name):
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-019', 'violation',
                        'parameter name only allows valid identifier syntax',
                        source_span=node.source_span,
                    ))

def check_canvas_shape(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-006: canvas shape validation."""
    if not ctx.sema.canvases():
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-006', 'violation',
            'workflow must have at least one canvas',
        ))
        return
    for canvas in ctx.sema.canvases():
        if not canvas.nodes and not canvas.edges:
            diagnostics.append(_diag_be(
                'SEMANTIC-BE-006', 'violation',
                'canvas schema must deserialize into backend semantic canvas shape',
            ))
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node._has_shape_issue:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-006', 'violation',
                    'canvas schema must deserialize into backend semantic canvas shape',
                    source_span=node.source_span,
                ))

def check_branch_ports(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-010: required branch/exception outgoing ports — checks all canvases."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.node_type == IF_NODE_TYPE_ID:
                outgoing = ctx.sema.edge_source_targets(node.node_id)
                source_ports = {e.source_port_id for e in outgoing if e.source_port_id}
                missing = []
                if 'true' not in source_ports:
                    missing.append('true')
                if 'false' not in source_ports:
                    missing.append('false')
                if missing:
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-010', 'violation',
                        'required branch/exception outgoing ports are not connected: ' + ', '.join(missing),
                        checkability=Checkability.PARTIAL,
                        source_span=node.source_span,
                    ))
            elif node.node_type == INTENT_NODE_TYPE_ID:
                outgoing = ctx.sema.edge_source_targets(node.node_id)
                if not outgoing:
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-010', 'violation',
                        'required branch/exception outgoing ports are not connected: intent',
                        checkability=Checkability.PARTIAL,
                        source_span=node.source_span,
                    ))

def check_nested_composites(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-016: nested composite nodes (Loop/Batch) are not allowed."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if (node.node_type == LOOP_NODE_TYPE_ID or node.node_type == BATCH_NODE_TYPE_ID) and node.blocks:
                for block in node.blocks:
                    if block.node_type == LOOP_NODE_TYPE_ID or block.node_type == BATCH_NODE_TYPE_ID:
                        diagnostics.append(_diag_be(
                            'SEMANTIC-BE-016', 'violation',
                            'composite nodes such as batch/loop cannot be nested',
                            checkability=Checkability.OFFLINE,
                            source_span=node.source_span,
                        ))

def check_global_variable_types(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-020: global variable type validation."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if ctx.sema.is_global_var_def(node.node_id):
                if not node.global_var_type:
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-020', 'violation',
                        'global variable definition must specify a type',
                        source_span=node.source_span,
                    ))

def check_type_compatibility(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-021: type compatibility for parameter assignments."""
    from ..sema.type_system import (
        infer_type, check_compatibility, CompatibilityState,
        canonicalize_type, extract_declared_type_from_param,
    )
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            for idx, param in enumerate(node.parameters):
                resolved = ctx.sema.resolved_ref_for(node.node_id, idx)
                if resolved is None or resolved.is_unresolved or not resolved.block_id:
                    continue
                # Skip global variable refs (runtime-deferred)
                if resolved.is_global:
                    continue
                # Source type: declared type on this parameter
                source_type_raw = extract_declared_type_from_param(param)
                if source_type_raw is None:
                    continue
                # Target type: declared type on the referenced node's output
                target_node = ctx.sema.node_by_id(resolved.block_id)
                if target_node is None:
                    continue
                target_type_raw = None
                ref_name = resolved.name
                if ref_name:
                    # Check parameters first
                    for tparam in target_node.parameters:
                        if tparam.name == ref_name:
                            target_type_raw = extract_declared_type_from_param(tparam)
                            break
                    # If not found in parameters, check outputs
                    if target_type_raw is None and target_node.outputs:
                        for out in target_node.outputs:
                            if out.name == ref_name and out.var_type:
                                target_type_raw = canonicalize_type(out.var_type)
                                break
                if target_type_raw is None:
                    continue
                # Compare
                source_fact = infer_type(source_type_raw)
                target_fact = infer_type(target_type_raw)
                compat = check_compatibility(source_fact, target_fact)
                if compat == CompatibilityState.INCOMPATIBLE:
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-021', 'warning',
                        f'type mismatch: parameter \'{param.name}\' expects '
                        f'\'{source_type_raw}\' but ref target \'{ref_name}\' '
                        f'is \'{target_type_raw}\'',
                        source_span=node.source_span,
                    ))

def check_start_connectivity(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-001: start node must have outgoing edges."""
    start_node = ctx.sema.node_by_id(START_NODE_ID)
    if start_node is None:
        return
    if not ctx.sema.has_outgoing_edges(START_NODE_ID):
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-001', 'violation',
            'start node must have at least one outgoing edge',
            source_span=start_node.source_span,
        ))

def check_node_connectivity(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-002: non-start/end nodes should have both incoming and outgoing edges.

    Excludes: start(1), end(2), comment(31), break(19), continue(29).
    Break and Continue are loop-control terminal nodes — they have no
    outgoing edges by design, matching coze-studio's skip:
        if et == entity.NodeTypeBreak || et == entity.NodeTypeContinue { continue }
    """
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.node_type in {NodeType.START, NodeType.END, NodeType.COMMENT, NodeType.BREAK, NodeType.CONTINUE}:
                continue
            has_incoming = ctx.sema.has_incoming_edges(node.node_id)
            has_outgoing = ctx.sema.has_outgoing_edges(node.node_id)
            if not has_incoming:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-002', 'violation',
                    f'node "{node.node_id}" has no incoming edges',
                    source_span=node.source_span,
                ))
            if not has_outgoing:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-002', 'violation',
                    f'node "{node.node_id}" has no outgoing edges',
                    source_span=node.source_span,
                ))

def check_edge_endpoints(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-003: edge source/target nodes must exist."""
    all_ids = ctx.sema.all_node_ids()
    for canvas in ctx.sema.canvases():
        for edge in canvas.edges:
            if edge.source_node_id not in all_ids:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-003', 'violation',
                    f'edge source node "{edge.source_node_id}" not found',
                    source_span=edge.source_span,
                ))
            if edge.target_node_id not in all_ids:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-003', 'violation',
                    f'edge target node "{edge.target_node_id}" not found',
                    source_span=edge.source_span,
                ))

def check_start_end_existence(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-004/005: start and end nodes must exist."""
    if ctx.sema.node_by_id(START_NODE_ID) is None:
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-004', 'violation',
            'start node (100001) must exist',
        ))
    if ctx.sema.node_by_id(END_NODE_ID) is None:
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-005', 'violation',
            'end node (900001) must exist',
        ))

def check_cycles(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-015: cycle detection — per-canvas, matching coze-studio DetectCycles.

    Each canvas is checked independently.  Only nodes belonging to that canvas
    participate in the adjacency graph; edges referencing nodes outside the
    canvas (e.g. inner→owner back-edges) are ignored, exactly as coze-studio
    builds nodeIDs from cv.cfg.Canvas.Nodes only.
    """
    for canvas in ctx.sema.canvases():
        canvas_node_ids = {node.node_id for node in canvas.nodes}

        # Build adjacency from edges, only for nodes in this canvas
        adjacency: dict[str, list[str]] = {}
        for edge in canvas.edges:
            # Only include edges where both endpoints are in this canvas
            if edge.source_node_id in canvas_node_ids and edge.target_node_id in canvas_node_ids:
                adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)

        visited: set[str] = set()
        in_stack: set[str] = set()
        found_cycle = False

        def _dfs(node_id: str) -> bool:
            nonlocal found_cycle
            if found_cycle:
                return True
            if node_id in in_stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            in_stack.add(node_id)
            for target in adjacency.get(node_id, []):
                if _dfs(target):
                    found_cycle = True
                    return True
            in_stack.discard(node_id)
            return False

        for node in canvas.nodes:
            if node.node_id not in visited:
                if _dfs(node.node_id):
                    diagnostics.append(_diag_be(
                        'SEMANTIC-BE-015', 'violation',
                        'workflow contains a cycle',
                        source_span=node.source_span,
                    ))
                    return

def check_ref_block_ids(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-017/018: reference blockID validation."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            # Input parameters — use ResolutionTable
            for idx, param in enumerate(node.parameters):
                resolved = ctx.sema.resolved_ref_for(node.node_id, idx)
                if resolved is not None:
                    check_resolved_ref(resolved, diagnostics, source_span=node.source_span)
            # Variable parameters — resolve inline
            for param in node.variable_parameters:
                if param.input_ref:
                    resolved = ctx.sema.resolve_full_ref(
                        param.input_ref.source,
                        param.input_ref.block_id,
                        param.input_ref.name,
                    )
                    check_resolved_ref(resolved, diagnostics, source_span=node.source_span)
            # Branch conditions — resolve inline
            for branch in node.branches:
                if branch.condition:
                    for cb in branch.condition.branches:
                        if cb.left and cb.left.input_ref and cb.left.input_ref.ref_type != 'literal':
                            resolved = ctx.sema.resolve_full_ref(
                                cb.left.input_ref.source,
                                cb.left.input_ref.block_id,
                                cb.left.input_ref.name,
                            )
                            check_resolved_ref(resolved, diagnostics, source_span=node.source_span)
                        if cb.right and cb.right.input_ref and cb.right.input_ref.ref_type != 'literal':
                            resolved = ctx.sema.resolve_full_ref(
                                cb.right.input_ref.source,
                                cb.right.input_ref.block_id,
                                cb.right.input_ref.name,
                            )
                            check_resolved_ref(resolved, diagnostics, source_span=node.source_span)

def check_resolved_ref(resolved, diagnostics: list[Diagnostic],
                        source_span: SourceSpan | None = None) -> None:
    """Check a pre-resolved reference for validity."""
    # Skip global variable refs (they use name-based lookup, blockID is optional)
    if resolved.is_global:
        return
    if resolved.is_unresolved:
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-017', 'violation',
            f'reference blockID "{resolved.block_id or ""}" does not point to an existing node',
            source_span=source_span,
        ))
    elif resolved.block_id is not None and isinstance(resolved.block_id, str) and resolved.block_id == '':
        diagnostics.append(_diag_be(
            'SEMANTIC-BE-017', 'violation',
            'reference blockID is empty',
            source_span=source_span,
        ))

def check_subworkflow_live_validation(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-022: subworkflow nodes require live validation."""
    for canvas in ctx.sema.canvases():
        for node in canvas.nodes:
            if node.node_type == SUBWORKFLOW_NODE_TYPE_ID:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-022', 'violation',
                    'subworkflow termination/version checks require live Coze validation',
                    checkability=Checkability.REQUIRES_LIVE_VALIDATION,
                    source_span=node.source_span,
                ))

def check_contract_consistency(ctx: PassContext, diagnostics: list[Diagnostic]) -> None:
    """BE-023: contract verification."""
    all_ids = ctx.sema.all_node_ids()
    for canvas in ctx.sema.canvases():
        for edge in canvas.edges:
            if edge.source_node_id not in all_ids:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-023', 'violation',
                    f'edge source node {edge.source_node_id} not found in node index',
                    source_span=edge.source_span,
                ))
            if edge.target_node_id not in all_ids:
                diagnostics.append(_diag_be(
                    'SEMANTIC-BE-023', 'violation',
                    f'edge target node {edge.target_node_id} not found in node index',
                    source_span=edge.source_span,
                ))

