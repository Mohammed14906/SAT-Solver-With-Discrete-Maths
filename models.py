"""
models.py
Core data structures for the SAT solver.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Literal:
    """A propositional variable, optionally negated."""
    name: str
    negated: bool = False

    def negate(self) -> "Literal":
        return Literal(self.name, not self.negated)

    def __str__(self) -> str:
        return f"¬{self.name}" if self.negated else self.name

    def __repr__(self) -> str:
        return str(self)


@dataclass(frozen=True)
class Clause:
    """A disjunction of literals (a single CNF clause)."""
    literals: frozenset[Literal]

    def __str__(self) -> str:
        if not self.literals:
            return "⊥"  # empty clause = False
        return " ∨ ".join(str(lit) for lit in sorted(self.literals, key=lambda l: (l.name, l.negated)))

    def __repr__(self) -> str:
        return f"Clause({str(self)})"

    def is_empty(self) -> bool:
        return len(self.literals) == 0

    def is_unit(self) -> bool:
        return len(self.literals) == 1

    def get_unit_literal(self) -> Optional[Literal]:
        if self.is_unit():
            return next(iter(self.literals))
        return None


@dataclass
class CNFFormula:
    """A conjunction of clauses (CNF form)."""
    clauses: list[Clause]
    variables: set[str]

    def __str__(self) -> str:
        if not self.clauses:
            return "⊤"  # empty formula = True
        return " ∧ ".join(f"({clause})" for clause in self.clauses)

    def is_empty(self) -> bool:
        return len(self.clauses) == 0

    def has_empty_clause(self) -> bool:
        return any(c.is_empty() for c in self.clauses)


@dataclass
class Assignment:
    """A mapping from variable names to truth values."""
    mapping: dict[str, bool] = field(default_factory=dict)

    def assign(self, name: str, value: bool) -> "Assignment":
        new_mapping = dict(self.mapping)
        new_mapping[name] = value
        return Assignment(new_mapping)

    def satisfies_literal(self, lit: Literal) -> Optional[bool]:
        """Returns True/False if literal is determined, None if unassigned."""
        if lit.name not in self.mapping:
            return None
        val = self.mapping[lit.name]
        return val if not lit.negated else not val

    def to_dict(self) -> dict[str, bool]:
        return dict(self.mapping)

    def __str__(self) -> str:
        items = sorted(self.mapping.items())
        return ", ".join(f"{k}={'T' if v else 'F'}" for k, v in items)


# ---------------------------------------------------------------------------
# AST node types for the formula parser
# ---------------------------------------------------------------------------

class ASTNode:
    """Base class for all AST nodes."""
    pass


@dataclass
class VarNode(ASTNode):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class NotNode(ASTNode):
    operand: ASTNode

    def __str__(self) -> str:
        return f"¬{self.operand}"


@dataclass
class AndNode(ASTNode):
    left: ASTNode
    right: ASTNode

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"


@dataclass
class OrNode(ASTNode):
    left: ASTNode
    right: ASTNode

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"


@dataclass
class ImpliesNode(ASTNode):
    left: ASTNode
    right: ASTNode

    def __str__(self) -> str:
        return f"({self.left} → {self.right})"


@dataclass
class IffNode(ASTNode):
    left: ASTNode
    right: ASTNode

    def __str__(self) -> str:
        return f"({self.left} ↔ {self.right})"
