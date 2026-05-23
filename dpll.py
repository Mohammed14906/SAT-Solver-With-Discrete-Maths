"""
dpll.py
Davis–Putnam–Logemann–Loveland (DPLL) SAT solver.

Features:
  - Unit propagation
  - Pure literal elimination
  - Chronological backtracking
  - Step-by-step trace for UI visualization
  - solve_first()  -> first satisfying Assignment | None
  - solve_all()    -> list of all satisfying Assignments
"""
from __future__ import annotations
from typing import Optional
from models import Literal, Clause, CNFFormula, Assignment

DECIDE    = "decide"
PROPAGATE = "propagate"
BACKTRACK = "backtrack"
CONFLICT  = "conflict"
SUCCESS   = "success"
PURE      = "pure"


def _make_step(kind: str, **kwargs) -> dict:
    return {"type": kind, **kwargs}


def _apply_assignment(formula: CNFFormula, lit: Literal) -> CNFFormula:
    """Simplify formula given that lit is True."""
    new_clauses = []
    for clause in formula.clauses:
        if lit in clause.literals:
            continue  # clause satisfied
        neg_lit = lit.negate()
        if neg_lit in clause.literals:
            reduced = frozenset(clause.literals - {neg_lit})
            new_clauses.append(Clause(reduced))
        else:
            new_clauses.append(clause)
    return CNFFormula(clauses=new_clauses, variables=formula.variables)


def _unit_propagate(formula, assignment, steps):
    changed = True
    while changed:
        changed = False
        for clause in formula.clauses:
            if clause.is_unit():
                unit_lit = clause.get_unit_literal()
                if unit_lit is None:
                    continue
                val = not unit_lit.negated
                steps.append(_make_step(PROPAGATE, literal=unit_lit.name, value=val, reason="unit clause"))
                assignment = assignment.assign(unit_lit.name, val)
                sat_lit = Literal(unit_lit.name, unit_lit.negated)
                formula = _apply_assignment(formula, sat_lit)
                changed = True
                break
    return formula, assignment


def _pure_literal_elim(formula, assignment, steps):
    pos_vars, neg_vars = set(), set()
    for clause in formula.clauses:
        for lit in clause.literals:
            (neg_vars if lit.negated else pos_vars).add(lit.name)

    changed = False
    for var in list(formula.variables):
        if var in assignment.mapping:
            continue
        is_pos = var in pos_vars
        is_neg = var in neg_vars
        if is_pos and not is_neg:
            val, sat_lit = True, Literal(var, False)
        elif is_neg and not is_pos:
            val, sat_lit = False, Literal(var, True)
        else:
            continue
        steps.append(_make_step(PURE, literal=var, value=val))
        assignment = assignment.assign(var, val)
        formula = _apply_assignment(formula, sat_lit)
        changed = True

    if changed:
        formula, assignment = _pure_literal_elim(formula, assignment, steps)
    return formula, assignment


def _pick_unassigned(formula: CNFFormula, assignment: Assignment) -> Optional[str]:
    for clause in formula.clauses:
        for lit in clause.literals:
            if lit.name not in assignment.mapping:
                return lit.name
    for var in sorted(formula.variables):
        if var not in assignment.mapping:
            return var
    return None


def _dpll(formula, assignment, steps, find_all, solutions) -> bool:
    formula, assignment = _unit_propagate(formula, assignment, steps)
    if not find_all:
        formula, assignment = _pure_literal_elim(formula, assignment, steps)

    if formula.has_empty_clause():
        steps.append(_make_step(CONFLICT))
        return False

    import itertools
    if formula.is_empty():
        unassigned = [v for v in formula.variables if v not in assignment.mapping]
        if not find_all:
            full = dict(assignment.mapping)
            for var in unassigned:
                full[var] = True
            final = Assignment(full)
            steps.append(_make_step(SUCCESS, assignment=final.to_dict()))
            solutions.append(final)
            return True
            
        # find_all is True: generate all combinations
        for vals in itertools.product([True, False], repeat=len(unassigned)):
            full = dict(assignment.mapping)
            for var, val in zip(unassigned, vals):
                full[var] = val
            final = Assignment(full)
            steps.append(_make_step(SUCCESS, assignment=final.to_dict()))
            solutions.append(final)
            # Add a small limit to prevent blowing up memory on huge trivial formulas
            if len(solutions) > 10000:
                break
        return False

    var = _pick_unassigned(formula, assignment)
    if var is None:
        steps.append(_make_step(CONFLICT))
        return False

    for val in (True, False):
        steps.append(_make_step(DECIDE, literal=var, value=val))
        sat_lit = Literal(var, False) if val else Literal(var, True)
        found = _dpll(
            _apply_assignment(formula, sat_lit),
            assignment.assign(var, val),
            steps, find_all, solutions
        )
        if found and not find_all:
            return True
        steps.append(_make_step(BACKTRACK, literal=var, value=val))

    return len(solutions) > 0


def solve_first(formula: CNFFormula) -> tuple[Optional[Assignment], list[dict]]:
    """Find the first satisfying assignment. Returns (assignment|None, steps)."""
    steps, solutions = [], []
    _dpll(formula, Assignment(), steps, find_all=False, solutions=solutions)
    return (solutions[0] if solutions else None), steps


def solve_all(formula: CNFFormula) -> tuple[list[Assignment], list[dict]]:
    """Enumerate all satisfying assignments. Returns (list[Assignment], steps)."""
    steps, solutions = [], []
    _dpll(formula, Assignment(), steps, find_all=True, solutions=solutions)
    return solutions, steps
