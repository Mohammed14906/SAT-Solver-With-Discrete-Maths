"""
utils.py
Utilities for truth table generation and formatting.
"""
from __future__ import annotations
from models import ASTNode, Assignment, VarNode, NotNode, AndNode, OrNode, ImpliesNode, IffNode

def _evaluate_ast(node: ASTNode, assignment: Assignment) -> bool:
    """Recursively evaluate an AST given an assignment."""
    if isinstance(node, VarNode):
        val = assignment.mapping.get(node.name)
        if val is None:
            raise ValueError(f"Variable {node.name} not in assignment")
        return val
    if isinstance(node, NotNode):
        return not _evaluate_ast(node.operand, assignment)
    if isinstance(node, AndNode):
        return _evaluate_ast(node.left, assignment) and _evaluate_ast(node.right, assignment)
    if isinstance(node, OrNode):
        return _evaluate_ast(node.left, assignment) or _evaluate_ast(node.right, assignment)
    if isinstance(node, ImpliesNode):
        return not _evaluate_ast(node.left, assignment) or _evaluate_ast(node.right, assignment)
    if isinstance(node, IffNode):
        return _evaluate_ast(node.left, assignment) == _evaluate_ast(node.right, assignment)
    raise TypeError(f"Unknown node type: {type(node)}")

def generate_truth_table(ast: ASTNode, variables: set[str], max_vars: int = 8) -> dict:
    """
    Generate a truth table for the given AST.
    Returns a dict with 'headers' and 'rows'.
    Limits to max_vars to prevent huge tables (2^8 = 256 rows).
    """
    vars_list = sorted(list(variables))
    if len(vars_list) > max_vars:
        return {
            "headers": vars_list + ["Result"],
            "rows": [["..."] * len(vars_list) + ["(Too many variables to display)"]]
        }

    headers = vars_list + ["Result"]
    rows = []
    
    n_vars = len(vars_list)
    for i in range(2**n_vars):
        # Create assignment for this row
        mapping = {}
        for j, var_name in enumerate(vars_list):
            # Check the j-th bit from the left
            bit_val = bool((i >> (n_vars - 1 - j)) & 1)
            mapping[var_name] = bit_val
            
        assignment = Assignment(mapping)
        try:
            result = _evaluate_ast(ast, assignment)
            row = [mapping[v] for v in vars_list] + [result]
            rows.append(row)
        except Exception:
            rows.append([mapping.get(v, False) for v in vars_list] + ["ERROR"])

    return {"headers": headers, "rows": rows}
