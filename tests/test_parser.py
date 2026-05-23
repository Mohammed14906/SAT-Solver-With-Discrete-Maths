"""
test_parser.py
"""
import pytest
from parser import parse_formula, get_variables
from models import VarNode, NotNode, AndNode, OrNode, ImpliesNode, IffNode

def test_parse_atoms():
    ast = parse_formula("P")
    assert isinstance(ast, VarNode)
    assert ast.name == "P"
    assert get_variables(ast) == {"P"}

def test_parse_not():
    ast = parse_formula("~P")
    assert isinstance(ast, NotNode)
    assert ast.operand.name == "P"

def test_parse_and_or():
    ast = parse_formula("P & Q | R")
    # | has lower precedence than &
    assert isinstance(ast, OrNode)
    assert isinstance(ast.left, AndNode)
    assert isinstance(ast.right, VarNode)

def test_parse_parens():
    ast = parse_formula("P & (Q | R)")
    assert isinstance(ast, AndNode)
    assert isinstance(ast.right, OrNode)

def test_parse_implies_iff():
    ast = parse_formula("P -> Q <-> R")
    # <-> has lowest precedence
    assert isinstance(ast, IffNode)
    assert isinstance(ast.left, ImpliesNode)

def test_unicode():
    ast = parse_formula("¬P ∧ (Q ∨ R) → S ↔ T")
    assert isinstance(ast, IffNode)
    assert get_variables(ast) == {"P", "Q", "R", "S", "T"}
