"""ASTVisitor — textbook Visitor pattern for Coze workflow AST.

Provides type-dispatched traversal of all AST node types.
Frozen dataclasses cannot hold methods, so accept() is a free function
that dispatches to the correct visit_* method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .workflow_ast import (
        BranchAST,
        CanvasAST,
        ConditionAST,
        ConditionBranchAST,
        EdgeAST,
        NodeAST,
        OutputVarAST,
        ParameterAST,
        RefAST,
        WorkflowAST,
    )


class ASTVisitor:
    """Base visitor with no-op defaults for all AST node types.

    Subclasses override visit_* methods to implement specific behavior.
    The default implementation does nothing (no-op), so inheriting classes
    only need to override the node types they care about.
    """

    # ── Top-level ──────────────────────────────────────────────

    def visit_workflow(self, node: WorkflowAST) -> None:
        """Visit a WorkflowAST node."""
        pass

    def visit_canvas(self, node: CanvasAST) -> None:
        """Visit a CanvasAST node."""
        pass

    # ── Node-level ─────────────────────────────────────────────

    def visit_node(self, node: NodeAST) -> None:
        """Visit a NodeAST node."""
        pass

    def visit_edge(self, node: EdgeAST) -> None:
        """Visit an EdgeAST node."""
        pass

    # ── Parameter-level ────────────────────────────────────────

    def visit_parameter(self, node: ParameterAST) -> None:
        """Visit a ParameterAST node."""
        pass

    def visit_ref(self, node: RefAST) -> None:
        """Visit a RefAST node."""
        pass

    # ── Output / Condition ─────────────────────────────────────

    def visit_output_var(self, node: OutputVarAST) -> None:
        """Visit an OutputVarAST node."""
        pass

    def visit_condition(self, node: ConditionAST) -> None:
        """Visit a ConditionAST node."""
        pass

    def visit_branch(self, node: BranchAST) -> None:
        """Visit a BranchAST node."""
        pass

    def visit_condition_branch(self, node: ConditionBranchAST) -> None:
        """Visit a ConditionBranchAST node."""
        pass


# ── accept() free function ────────────────────────────────────

def accept(visitor: ASTVisitor, node) -> None:
    """Dispatch node to the correct visit_* method, then recurse into children.

    This is the textbook accept() for frozen dataclasses that cannot hold methods.
    """
    from .workflow_ast import (
        BranchAST,
        CanvasAST,
        ConditionAST,
        ConditionBranchAST,
        EdgeAST,
        NodeAST,
        OutputVarAST,
        ParameterAST,
        RefAST,
        WorkflowAST,
    )

    if isinstance(node, WorkflowAST):
        visitor.visit_workflow(node)
        accept(visitor, node.root_canvas)
        for canvas in node.canvases:
            if canvas is not node.root_canvas:
                accept(visitor, canvas)

    elif isinstance(node, CanvasAST):
        visitor.visit_canvas(node)
        for param in node.parameters:
            accept(visitor, param)
        for edge in node.edges:
            accept(visitor, edge)
        for child_node in node.nodes:
            accept(visitor, child_node)

    elif isinstance(node, NodeAST):
        visitor.visit_node(node)
        for param in node.parameters:
            accept(visitor, param)
        for param in node.variable_parameters:
            accept(visitor, param)
        for param in node.node_specific_params:
            accept(visitor, param)
        for branch in node.branches:
            accept(visitor, branch)
        for out in node.outputs:
            accept(visitor, out)
        for block in node.blocks:
            accept(visitor, block)
        for edge in node.nested_edges:
            accept(visitor, edge)

    elif isinstance(node, EdgeAST):
        visitor.visit_edge(node)

    elif isinstance(node, ParameterAST):
        visitor.visit_parameter(node)
        if node.input_ref is not None:
            accept(visitor, node.input_ref)
        if node.left_ref is not None:
            accept(visitor, node.left_ref)
        if node.right_ref is not None:
            accept(visitor, node.right_ref)

    elif isinstance(node, RefAST):
        visitor.visit_ref(node)

    elif isinstance(node, OutputVarAST):
        visitor.visit_output_var(node)
        for child in node.children:
            accept(visitor, child)

    elif isinstance(node, BranchAST):
        visitor.visit_branch(node)
        if node.condition is not None:
            accept(visitor, node.condition)

    elif isinstance(node, ConditionAST):
        visitor.visit_condition(node)
        for branch in node.branches:
            accept(visitor, branch)

    elif isinstance(node, ConditionBranchAST):
        visitor.visit_condition_branch(node)
        if node.left is not None:
            accept(visitor, node.left)
        if node.right is not None:
            accept(visitor, node.right)
