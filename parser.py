"""
parser.py
Tokenizes and parses propositional logic formulas into an AST.

Supported operators (ASCII and Unicode):
  Negation      :  ~  !  NOT  ¬
  Conjunction   :  &  AND  ∧
  Disjunction   :  |  OR   ∨
  Implication   :  ->  IMPLIES  →
  Biconditional :  <->  IFF  ↔

Precedence (lowest to highest):
  1. ↔
  2. →
  3. ∧
  4. ∨
  5. ¬ (unary)
  6. atoms / parentheses
"""
from __future__ import annotations
import re
from typing import List
from models import (
    ASTNode, VarNode, NotNode, AndNode, OrNode, ImpliesNode, IffNode
)

# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------
TK_VAR     = "VAR"
TK_NOT     = "NOT"
TK_AND     = "AND"
TK_OR      = "OR"
TK_IMPLIES = "IMPLIES"
TK_IFF     = "IFF"
TK_LPAREN  = "LPAREN"
TK_RPAREN  = "RPAREN"
TK_EOF     = "EOF"


class Token:
    __slots__ = ("type", "value")

    def __init__(self, type_: str, value: str = ""):
        self.type = type_
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r})"


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

_TOKEN_PATTERNS: List[tuple[str, str]] = [
    # Multi-char operators first to avoid partial matches
    (TK_IFF,     r"<->|↔|IFF\b"),
    (TK_IMPLIES, r"->|→|IMPLIES\b"),
    (TK_NOT,     r"~|!|¬|NOT\b"),
    (TK_AND,     r"&{1,2}|∧|AND\b"),
    (TK_OR,      r"\|{1,2}|∨|OR\b"),
    (TK_LPAREN,  r"\("),
    (TK_RPAREN,  r"\)"),
    # Variable: starts with letter, may contain letters, digits, underscores
    (TK_VAR,     r"[A-Za-z_][A-Za-z0-9_]*"),
]

_MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_PATTERNS),
    re.UNICODE
)


def tokenize(text: str) -> List[Token]:
    """Convert a formula string into a list of Tokens."""
    tokens: List[Token] = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        # Skip whitespace
        if text[pos].isspace():
            pos += 1
            continue
        m = _MASTER_PATTERN.match(text, pos)
        if not m:
            raise SyntaxError(
                f"Unexpected character {text[pos]!r} at position {pos}"
            )
        kind = m.lastgroup
        tokens.append(Token(kind, m.group()))
        pos = m.end()
    tokens.append(Token(TK_EOF))
    return tokens


# ---------------------------------------------------------------------------
# Parser  (recursive-descent, follows the precedence table)
# ---------------------------------------------------------------------------

class Parser:
    """
    Recursive-descent parser for propositional logic.

    Grammar (lowest precedence first):
        formula   ::= iff
        iff       ::= implies (IFF implies)*
        implies   ::= or (IMPLIES or)*
        and_expr  ::= or (AND or)*
        or_expr   ::= not_expr (OR not_expr)*
        not_expr  ::= NOT not_expr | atom
        atom      ::= VAR | '(' formula ')'
    """

    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0

    # -- helpers -------------------------------------------------------------

    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self, expected_type: str | None = None) -> Token:
        tok = self._current
        if expected_type and tok.type != expected_type:
            raise SyntaxError(
                f"Expected {expected_type} but got {tok.type!r} ({tok.value!r})"
            )
        self._pos += 1
        return tok

    def _match(self, *types: str) -> bool:
        return self._current.type in types

    # -- grammar rules -------------------------------------------------------

    def parse(self) -> ASTNode:
        node = self._parse_iff()
        if not self._match(TK_EOF):
            raise SyntaxError(
                f"Unexpected token after formula: {self._current!r}"
            )
        return node

    def _parse_iff(self) -> ASTNode:
        left = self._parse_implies()
        while self._match(TK_IFF):
            self._consume()
            right = self._parse_implies()
            left = IffNode(left, right)
        return left

    def _parse_implies(self) -> ASTNode:
        left = self._parse_or()
        while self._match(TK_IMPLIES):
            self._consume()
            right = self._parse_or()
            left = ImpliesNode(left, right)
        return left

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._match(TK_OR):
            self._consume()
            right = self._parse_and()
            left = OrNode(left, right)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        while self._match(TK_AND):
            self._consume()
            right = self._parse_not()
            left = AndNode(left, right)
        return left

    def _parse_not(self) -> ASTNode:
        if self._match(TK_NOT):
            self._consume()
            operand = self._parse_not()
            return NotNode(operand)
        return self._parse_atom()

    def _parse_atom(self) -> ASTNode:
        if self._match(TK_VAR):
            tok = self._consume()
            return VarNode(tok.value)
        if self._match(TK_LPAREN):
            self._consume()
            node = self._parse_iff()
            self._consume(TK_RPAREN)
            return node
        raise SyntaxError(
            f"Expected variable or '(' but got {self._current!r}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_formula(text: str) -> ASTNode:
    """
    Parse a propositional logic formula string and return its AST.

    Raises SyntaxError on invalid input.
    """
    tokens = tokenize(text)
    return Parser(tokens).parse()


def get_variables(node: ASTNode) -> set[str]:
    """Collect all variable names from an AST."""
    if isinstance(node, VarNode):
        return {node.name}
    if isinstance(node, NotNode):
        return get_variables(node.operand)
    if isinstance(node, (AndNode, OrNode, ImpliesNode, IffNode)):
        return get_variables(node.left) | get_variables(node.right)
    return set()
