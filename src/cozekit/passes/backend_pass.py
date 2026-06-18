"""BackendPass — SEMANTIC-BE-* rules.

Validates backend-oriented semantic rules: graph connectivity, cycles,
reference integrity, type compatibility, contract consistency.
"""

from __future__ import annotations

from ..diagnostics.core import Diagnostic
from .context import PassContext
from .graph_validators import (
    check_branch_ports,
    check_canvas_shape,
    check_contract_consistency,
    check_cycles,
    check_edge_endpoints,
    check_global_variable_types,
    check_isolated_nodes,
    check_nested_composites,
    check_node_connectivity,
    check_parameter_names,
    check_ref_block_ids,
    check_start_connectivity,
    check_start_end_existence,
    check_subworkflow_live_validation,
    check_type_compatibility,
)
from .io_validators import check_global_array_element_type


class BackendPass:
    """SEMANTIC-BE-* rules: connectivity, cycles, refs, type compat."""

    requires_document: bool = False

    @property
    def name(self) -> str:
        return 'semantic-be'

    def run(self, ctx: PassContext) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []

        check_isolated_nodes(ctx, diagnostics)
        check_parameter_names(ctx, diagnostics)
        check_canvas_shape(ctx, diagnostics)
        check_branch_ports(ctx, diagnostics)
        check_nested_composites(ctx, diagnostics)
        check_global_variable_types(ctx, diagnostics)
        check_type_compatibility(ctx, diagnostics)
        check_start_connectivity(ctx, diagnostics)
        check_node_connectivity(ctx, diagnostics)
        check_edge_endpoints(ctx, diagnostics)
        check_start_end_existence(ctx, diagnostics)
        check_cycles(ctx, diagnostics)
        check_ref_block_ids(ctx, diagnostics)
        check_subworkflow_live_validation(ctx, diagnostics)
        check_contract_consistency(ctx, diagnostics)

        # BE-021: global array element type
        check_global_array_element_type(ctx, diagnostics)

        return tuple(diagnostics)
