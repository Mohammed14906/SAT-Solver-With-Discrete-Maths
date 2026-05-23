"""
dimacs.py
Reader for the DIMACS CNF file format (standard SAT benchmark format).

Format example:
    c This is a comment
    p cnf 3 3
    1 2 0
    -1 3 0
    -2 -3 0

Variable names are mapped to x1, x2, ... xN.
"""
from __future__ import annotations
from models import Literal, Clause, CNFFormula


def parse_dimacs(text: str) -> CNFFormula:
    """
    Parse DIMACS CNF text and return a CNFFormula.
    Raises ValueError on malformed input.
    """
    clauses: list[Clause] = []
    num_vars = 0
    num_clauses = 0
    header_found = False
    current_literals: list[Literal] = []

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("c"):
            continue  # comment
        if line.startswith("p"):
            parts = line.split()
            if len(parts) < 4 or parts[1] != "cnf":
                raise ValueError(f"Line {line_no}: invalid problem line: {line!r}")
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            header_found = True
            continue

        if not header_found:
            raise ValueError(f"Line {line_no}: data before problem line")

        # Parse literal tokens
        tokens = line.split()
        for tok in tokens:
            n = int(tok)
            if n == 0:
                # End of clause
                clauses.append(Clause(frozenset(current_literals)))
                current_literals = []
            else:
                name = f"x{abs(n)}"
                current_literals.append(Literal(name, negated=(n < 0)))

    # Handle missing trailing 0
    if current_literals:
        clauses.append(Clause(frozenset(current_literals)))

    if not header_found:
        raise ValueError("No problem line (p cnf ...) found in DIMACS file")

    variables = {f"x{i}" for i in range(1, num_vars + 1)}
    return CNFFormula(clauses=clauses, variables=variables)
