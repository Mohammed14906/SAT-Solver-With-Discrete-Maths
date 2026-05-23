# SAT Solver Pro

A Boolean Satisfiability (SAT) problem solver built with Python and a modern web UI.

Given a propositional logic formula, the solver determines whether there exists at least one assignment of truth values to variables that makes the formula true.

---

## Features

- **DPLL Algorithm** — Davis–Putnam–Logemann–Loveland solver with:
  - Unit propagation
  - Pure literal elimination
  - Chronological backtracking
  - Step-by-step execution trace
- **Formula Parser** — Accepts both ASCII and Unicode logical operators:
  | Operator       | ASCII         | Unicode |
  |----------------|---------------|---------|
  | Negation       | `~`, `!`, `NOT` | `¬`   |
  | Conjunction    | `&`, `AND`    | `∧`     |
  | Disjunction    | `\|`, `OR`    | `∨`     |
  | Implication    | `->`, `IMPLIES` | `→`   |
  | Biconditional  | `<->`, `IFF`  | `↔`     |
- **CNF Conversion** — Automatically converts any formula to Conjunctive Normal Form
- **Two Solve Modes** — Find the *first* satisfying assignment, or enumerate *all* of them
- **Truth Table** — Auto-generated for formulas with ≤ 8 variables
- **DIMACS Upload** — Drag & drop standard `.cnf` benchmark files

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the web app

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

### 3. Run the tests

```bash
python -m pytest tests/ -v
```

---

## Example

Formula from the project specification:

```
(P | Q) & (~P | R) & (~Q | ~R)
```

**Result:** SATISFIABLE  
**First solution:** `P = False, Q = True, R = False`  
**All solutions:** 2 (also `P = True, Q = False, R = True`)

---

## Project Structure

```
sat_solver/
├── app.py          # Flask web server & REST API
├── parser.py       # Recursive-descent formula parser → AST
├── cnf.py          # AST → CNF conversion (4-step pipeline)
├── dpll.py         # DPLL solver with step tracer
├── dimacs.py       # DIMACS .cnf file reader
├── models.py       # Data classes (Literal, Clause, CNFFormula, etc.)
├── utils.py        # Truth table generator
├── requirements.txt
├── conftest.py     # pytest path setup
├── tests/
│   ├── test_parser.py
│   ├── test_cnf.py
│   └── test_dpll.py
└── static/
    ├── index.html  # Single-page app
    ├── style.css   # Glassmorphism dark UI
    └── app.js      # Frontend logic & DPLL trace renderer
```

---

## Algorithm Overview

```
Input formula string
        │
        ▼
  [parser.py]  Tokenize + parse → Abstract Syntax Tree (AST)
        │
        ▼
  [cnf.py]     Eliminate ↔ → Eliminate → → Push ¬ inward → Distribute ∨ over ∧
        │
        ▼
  [dpll.py]    DPLL: Unit Propagate → Pure Literal Elim → Branch → Backtrack
        │
        ▼
  SAT (assignment) | UNSAT
```
