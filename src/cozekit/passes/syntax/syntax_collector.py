"""SyntaxFactCollector — Visitor-based structural fact collection.

Traverses the AST using the Visitor pattern to collect structural facts
that SyntaxPass needs for its rules. This replaces ad-hoc iteration with
a textbook Visitor approach.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ...ast.visitor import ASTVisitor, accept
from ...ast.workflow_ast import (
    CanvasAST, EdgeAST, NodeAST, OutputVarAST,
    ParameterAST, RefAST, WorkflowAST,
)


@dataclass
class SyntaxFacts:
    """Collected structural facts from AST traversal."""
    # Counts
    canvas_count: int = 0
    node_count: int = 0
    edge_count: int = 0
    non_object_node_count: int = 0
    has_nodes: bool = False
    has_edges: bool = False

    # Per-canvas
    canvas_node_ids: dict[str, list[str]] = field(default_factory=dict)  # canvas_path -> [node_ids]
    canvas_edge_list: dict[str, list[EdgeAST]] = field(default_factory=dict)  # canvas_path -> [edges]
    canvas_node_map: dict[str, dict[str, NodeAST]] = field(default_factory=dict)  # canvas_path -> {id: node}

    # Global
    all_nodes: list[NodeAST] = field(default_factory=list)
    all_edges: list[EdgeAST] = field(default_factory=list)
    all_node_ids: list[str] = field(default_factory=list)

    # Duplicate detection
    duplicate_node_ids: list[tuple[str, str]] = field(default_factory=list)  # (canvas_path, node_id)

    # Branch nodes needing sourcePortID
    branch_nodes_without_port: list[tuple[EdgeAST, NodeAST]] = field(default_factory=list)

    # Node-specific facts
    start_nodes: list[NodeAST] = field(default_factory=list)
    end_nodes: list[NodeAST] = field(default_factory=list)
    variable_nodes: list[NodeAST] = field(default_factory=list)

    # Parameters with refs
    params_with_refs: list[tuple[NodeAST, ParameterAST, RefAST]] = field(default_factory=list)


class SyntaxFactCollector(ASTVisitor):
    """Collects structural facts from the AST using Visitor pattern.

    Usage:
        collector = SyntaxFactCollector()
        accept(collector, workflow_ast)
        facts = collector.facts
    """

    def __init__(self) -> None:
        self.facts = SyntaxFacts()
        self._current_canvas_path: str = ''

    def visit_workflow(self, node: WorkflowAST) -> None:
        pass

    def visit_canvas(self, node: CanvasAST) -> None:
        self.facts.canvas_count += 1
        path = str(node.canvas_path)
        self._current_canvas_path = path
        self.facts.canvas_node_ids[path] = []
        self.facts.canvas_edge_list[path] = []
        self.facts.canvas_node_map[path] = {}

    def visit_node(self, node: NodeAST) -> None:
        self.facts.node_count += 1
        self.facts.has_nodes = True
        self.facts.all_nodes.append(node)
        self.facts.all_node_ids.append(node.node_id)
        self.facts.non_object_node_count += node.non_object_node_count

        path = self._current_canvas_path
        if path in self.facts.canvas_node_ids:
            # Check duplicate
            if node.node_id in self.facts.canvas_node_map.get(path, {}):
                self.facts.duplicate_node_ids.append((path, node.node_id))
            self.facts.canvas_node_ids[path].append(node.node_id)
            self.facts.canvas_node_map[path][node.node_id] = node

        # Classify by type
        if node.node_type == '1':
            self.facts.start_nodes.append(node)
        elif node.node_type == '2':
            self.facts.end_nodes.append(node)
        elif node.node_type == '11':
            self.facts.variable_nodes.append(node)

    def visit_edge(self, node: EdgeAST) -> None:
        self.facts.edge_count += 1
        self.facts.has_edges = True
        self.facts.all_edges.append(node)
        path = self._current_canvas_path
        if path in self.facts.canvas_edge_list:
            self.facts.canvas_edge_list[path].append(node)

    def visit_parameter(self, node: ParameterAST) -> None:
        pass

    def visit_ref(self, node: RefAST) -> None:
        pass

    def visit_output_var(self, node: OutputVarAST) -> None:
        pass
