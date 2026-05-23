"""
test_cnf.py
"""
import pytest
from parser import parse_formula
from cnf import ast_to_cnf

def test_cnf_simple_or():
    ast = parse_formula("P | Q")
    cnf = ast_to_cnf(ast)
    assert len(cnf.clauses) == 1
    literals = {l.name for l in cnf.clauses[0].literals}
    assert literals == {"P", "Q"}

def test_cnf_implies():
    ast = parse_formula("P -> Q")
    cnf = ast_to_cnf(ast)
    # ~P | Q
    assert len(cnf.clauses) == 1
    lits = cnf.clauses[0].literals
    assert len(lits) == 2

def test_cnf_demorgan():
    ast = parse_formula("~(P & Q)")
    cnf = ast_to_cnf(ast)
    # ~P | ~Q
    assert len(cnf.clauses) == 1

def test_cnf_distribute():
    ast = parse_formula("P | (Q & R)")
    cnf = ast_to_cnf(ast)
    # (P | Q) & (P | R)
    assert len(cnf.clauses) == 2

def test_tautology_elimination():
    ast = parse_formula("P | ~P")
    cnf = ast_to_cnf(ast)
    # Tautologies should be removed, leaving an empty formula (True)
    assert len(cnf.clauses) == 0
