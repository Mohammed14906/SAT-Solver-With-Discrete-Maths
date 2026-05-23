"""
test_dpll.py
"""
import pytest
from parser import parse_formula
from cnf import ast_to_cnf
from dpll import solve_first, solve_all

def _solve(formula_str):
    ast = parse_formula(formula_str)
    cnf = ast_to_cnf(ast)
    return solve_first(cnf)

def test_dpll_sat():
    sol, steps = _solve("(P | Q) & (~P | R) & (~Q | ~R)")
    assert sol is not None
    # Check if assignment actually satisfies the formula
    p, q, r = sol.mapping['P'], sol.mapping['Q'], sol.mapping.get('R', True)
    assert (p or q) and (not p or r) and (not q or not r)

def test_dpll_unsat():
    sol, steps = _solve("P & ~P")
    assert sol is None

def test_dpll_unsat_complex():
    sol, steps = _solve("(P | Q) & ~P & ~Q")
    assert sol is None

def test_dpll_tautology():
    sol, steps = _solve("P | ~P")
    assert sol is not None

def test_solve_all():
    ast = parse_formula("P | Q")
    cnf = ast_to_cnf(ast)
    sols, steps = solve_all(cnf)
    assert len(sols) == 3 # (T,T), (T,F), (F,T)

def test_solve_all_implies():
    ast = parse_formula("P -> Q")
    cnf = ast_to_cnf(ast)
    sols, steps = solve_all(cnf)
    assert len(sols) == 3 # (F,F), (F,T), (T,T)
