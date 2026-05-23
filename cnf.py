"""
cnf.py
Converts a propositional AST into Conjunctive Normal Form (CNF).

Steps (all performed on the AST level before clause extraction):
  1. Eliminate biconditionals  (A ↔ B  →  (A → B) ∧ (B → A))
  2. Eliminate implications    (A → B  →  ¬A ∨ B)
  3. Push negations inward     (De Morgan's laws + double-negation)
  4. Distribute OR over AND    (A ∨ (B ∧ C)  →  (A ∨ B) ∧ (A ∨ C))
  5. Extract clauses           (flatten the resulting AND-tree)
"""
from __future__ import annotations
from models import (
    ASTNode, VarNode, NotNode, AndNode, OrNode, ImpliesNode, IffNode,
    Literal, Clause, CNFFormula
)
from parser import get_variables


# ---------------------------------------------------------------------------
# Step 1 & 2 – Eliminate ↔ and →
# ---------------------------------------------------------------------------

def _elim_connectives(node: ASTNode) -> ASTNode:
    if isinstance(node, VarNode):
        return node

    if isinstance(node, NotNode):
        return NotNode(_elim_connectives(node.operand))

    if isinstance(node, AndNode):
        return AndNode(_elim_connectives(node.left), _elim_connectives(node.right))

    if isinstance(node, OrNode):
        return OrNode(_elim_connectives(node.left), _elim_connectives(node.right))

    if isinstance(node, ImpliesNode):
        # A → B  ≡  ¬A ∨ B
        return OrNode(
            NotNode(_elim_connectives(node.left)),
            _elim_connectives(node.right)
        )

    if isinstance(node, IffNode):
        # A ↔ B  ≡  (A → B) ∧ (B → A)
        a = _elim_connectives(node.left)
        b = _elim_connectives(node.right)
        return AndNode(
            OrNode(NotNode(a), b),
            OrNode(NotNode(b), a)
        )

    raise TypeError(f"Unknown AST node type: {type(node)}")


# ---------------------------------------------------------------------------
# Step 3 – Push negations inward (NNF)
# ---------------------------------------------------------------------------

def _to_nnf(node: ASTNode) -> ASTNode:
    if isinstance(node, VarNode):
        return node

    if isinstance(node, AndNode):
        return AndNode(_to_nnf(node.left), _to_nnf(node.right))

    if isinstance(node, OrNode):
        return OrNode(_to_nnf(node.left), _to_nnf(node.right))

    if isinstance(node, NotNode):
        inner = node.operand

        if isinstance(inner, VarNode):
            return node  # ¬P stays as ¬P

        if isinstance(inner, NotNode):
            # ¬¬A  ≡  A
            return _to_nnf(inner.operand)

        if isinstance(inner, AndNode):
            # ¬(A ∧ B)  ≡  ¬A ∨ ¬B
            return OrNode(_to_nnf(NotNode(inner.left)), _to_nnf(NotNode(inner.right)))

        if isinstance(inner, OrNode):
            # ¬(A ∨ B)  ≡  ¬A ∧ ¬B
            return AndNode(_to_nnf(NotNode(inner.left)), _to_nnf(NotNode(inner.right)))

        raise TypeError(
            f"_to_nnf: unexpected inner node after connective elimination: {type(inner)}"
        )

    raise TypeError(f"_to_nnf: unexpected node type: {type(node)}")


# ---------------------------------------------------------------------------
# Step 4 – Distribute OR over AND
# ---------------------------------------------------------------------------

def _distribute(node: ASTNode) -> ASTNode:
    if isinstance(node, (VarNode, NotNode)):
        return node

    if isinstance(node, AndNode):
        return AndNode(_distribute(node.left), _distribute(node.right))

    if isinstance(node, OrNode):
        left  = _distribute(node.left)
        right = _distribute(node.right)

        # (A ∧ B) ∨ C  →  (A ∨ C) ∧ (B ∨ C)
        if isinstance(left, AndNode):
            return AndNode(
                _distribute(OrNode(left.left, right)),
                _distribute(OrNode(left.right, right))
            )

        # A ∨ (B ∧ C)  →  (A ∨ B) ∧ (A ∨ C)
        if isinstance(right, AndNode):
            return AndNode(
                _distribute(OrNode(left, right.left)),
                _distribute(OrNode(left, right.right))
            )

        return OrNode(left, right)

    raise TypeError(f"_distribute: unexpected node: {type(node)}")


# ---------------------------------------------------------------------------
# Step 5 – Extract clauses from the AND-OR tree
# ---------------------------------------------------------------------------

def _extract_clauses(node: ASTNode) -> list[Clause]:
    """Flatten AND-tree into a list of Clauses; each OR-branch is one clause."""
    if isinstance(node, AndNode):
        return _extract_clauses(node.left) + _extract_clauses(node.right)

    # A single disjunction (or single literal) → one clause
    literals = _collect_literals(node)
    return [Clause(frozenset(literals))]


def _collect_literals(node: ASTNode) -> list[Literal]:
    if isinstance(node, VarNode):
        return [Literal(node.name, False)]

    if isinstance(node, NotNode):
        inner = node.operand
        if isinstance(inner, VarNode):
            return [Literal(inner.name, True)]
        raise ValueError(f"Non-literal in clause after CNF conversion: {node}")

    if isinstance(node, OrNode):
        return _collect_literals(node.left) + _collect_literals(node.right)

    raise ValueError(f"Unexpected node in clause: {type(node)}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ast_to_cnf(ast: ASTNode) -> CNFFormula:
    """
    Convert a parsed AST into a CNFFormula.

    Pipeline:
        AST  →  [elim ↔/→]  →  [NNF]  →  [distribute]  →  [extract clauses]
    """
    step1 = _elim_connectives(ast)
    step2 = _to_nnf(step1)
    step3 = _distribute(step2)
    clauses = _extract_clauses(step3)

    # Remove tautological clauses (contain both P and ¬P)
    clean_clauses = []
    for clause in clauses:
        names_pos = {lit.name for lit in clause.literals if not lit.negated}
        names_neg = {lit.name for lit in clause.literals if lit.negated}
        if names_pos & names_neg:
            continue  # tautology, always true — safe to drop
        clean_clauses.append(clause)

    variables = get_variables(ast)
    return CNFFormula(clauses=clean_clauses, variables=variables)
