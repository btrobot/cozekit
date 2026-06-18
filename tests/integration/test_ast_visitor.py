"""Tests for ASTVisitor pattern."""
import pytest
from cozekit.ast.visitor import ASTVisitor, accept
from cozekit.ast.workflow_ast import (
    BranchAST, CanvasAST, ConditionAST, ConditionBranchAST,
    EdgeAST, NodeAST, OutputVarAST, ParameterAST, RefAST, WorkflowAST,
)


class TestVisitorDefaults:
    """All visit_* methods exist and are no-op."""

    def test_all_visit_methods_exist(self):
        v = ASTVisitor()
        # Should not raise
        v.visit_workflow(WorkflowAST())
        v.visit_canvas(CanvasAST())
        v.visit_node(NodeAST(node_id='x', node_type='1'))
        v.visit_edge(EdgeAST(source_node_id='a', target_node_id='b'))
        v.visit_parameter(ParameterAST(name='p'))
        v.visit_ref(RefAST(ref_type='block'))
        v.visit_output_var(OutputVarAST(name='o'))
        v.visit_condition(ConditionAST())
        v.visit_branch(BranchAST())
        v.visit_condition_branch(ConditionBranchAST())


class TestAcceptTraversal:
    """accept() correctly traverses AST structure."""

    def test_workflow_visits_root_canvas(self):
        visited = []
        class C(ASTVisitor):
            def visit_workflow(self, node): visited.append('wf')
            def visit_canvas(self, node): visited.append('canvas')
        
        wf = WorkflowAST(root_canvas=CanvasAST(), canvases=())
        accept(C(), wf)
        assert 'wf' in visited
        assert 'canvas' in visited

    def test_canvas_visits_nodes_and_edges(self):
        visited = []
        class C(ASTVisitor):
            def visit_node(self, node): visited.append(('node', node.node_id))
            def visit_edge(self, node): visited.append(('edge', node.source_node_id))
        
        canvas = CanvasAST(
            nodes=(NodeAST(node_id='n1', node_type='1'), NodeAST(node_id='n2', node_type='2')),
            edges=(EdgeAST(source_node_id='n1', target_node_id='n2'),),
        )
        accept(C(), canvas)
        assert ('node', 'n1') in visited
        assert ('node', 'n2') in visited
        assert ('edge', 'n1') in visited

    def test_node_visits_parameters(self):
        visited = []
        class C(ASTVisitor):
            def visit_parameter(self, node): visited.append(('param', node.name))
        
        node = NodeAST(
            node_id='n1', node_type='3',
            parameters=(ParameterAST(name='prompt'), ParameterAST(name='systemPrompt')),
        )
        accept(C(), node)
        assert ('param', 'prompt') in visited
        assert ('param', 'systemPrompt') in visited

    def test_parameter_visits_input_ref(self):
        visited = []
        class C(ASTVisitor):
            def visit_ref(self, node): visited.append(('ref', node.ref_type))
        
        param = ParameterAST(name='p', input_ref=RefAST(ref_type='block', block_id='100', name='out'))
        accept(C(), param)
        assert ('ref', 'block') in visited

    def test_node_visits_outputs(self):
        visited = []
        class C(ASTVisitor):
            def visit_output_var(self, node): visited.append(('out', node.name))
        
        node = NodeAST(
            node_id='100001', node_type='1',
            outputs=(OutputVarAST(name='out1', var_type='string'),),
        )
        accept(C(), node)
        assert ('out', 'out1') in visited

    def test_output_var_visits_children(self):
        visited = []
        class C(ASTVisitor):
            def visit_output_var(self, node): visited.append(('out', node.name))
        
        child = OutputVarAST(name='child1', var_type='string')
        parent = OutputVarAST(name='parent', var_type='object', children=(child,))
        node = NodeAST(node_id='n', node_type='1', outputs=(parent,))
        accept(C(), node)
        assert ('out', 'parent') in visited
        assert ('out', 'child1') in visited

    def test_node_visits_nested_blocks(self):
        visited = []
        class C(ASTVisitor):
            def visit_node(self, node): visited.append(('node', node.node_id))
        
        inner = NodeAST(node_id='inner', node_type='22')
        outer = NodeAST(node_id='outer', node_type='21', blocks=(inner,))
        accept(C(), outer)
        assert ('node', 'outer') in visited
        assert ('node', 'inner') in visited

    def test_empty_workflow(self):
        visited = []
        class C(ASTVisitor):
            def visit_workflow(self, node): visited.append('wf')
        
        wf = WorkflowAST(root_canvas=CanvasAST(), canvases=())
        accept(C(), wf)
        assert 'wf' in visited

    def test_condition_branch_visits_operands(self):
        visited = []
        class C(ASTVisitor):
            def visit_parameter(self, node): visited.append(('param', node.name))
        
        cb = ConditionBranchAST(
            left=ParameterAST(name='left_val'),
            operator='==',
            right=ParameterAST(name='right_val'),
        )
        cond = ConditionAST(branches=(cb,))
        branch = BranchAST(branch_key='true', condition=cond)
        accept(C(), branch)
        assert ('param', 'left_val') in visited
        assert ('param', 'right_val') in visited

    def test_nested_canvases_visited_once(self):
        """Root canvas in .canvases tuple should not be visited twice."""
        visit_count = []
        class C(ASTVisitor):
            def visit_canvas(self, node): visit_count.append(node.canvas_path)
        
        root = CanvasAST(canvas_path=(), nodes=())
        wf = WorkflowAST(root_canvas=root, canvases=(root,))
        accept(C(), wf)
        # Root canvas visited exactly once (dedup logic in accept)
        assert len(visit_count) == 1
