"""
app.py
Flask web server for the SAT solver.
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from parser import parse_formula, get_variables
from cnf import ast_to_cnf
from dpll import solve_first, solve_all
from dimacs import parse_dimacs
from utils import generate_truth_table

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/solve", methods=["POST"])
def solve():
    data = request.get_json()
    if not data or "formula" not in data:
        return jsonify({"status": "ERROR", "message": "No formula provided"}), 400

    # --- Input Sanitization ---
    formula_str = data["formula"]
    formula_str = formula_str.strip()
    # Normalize non-breaking spaces and other Unicode spaces
    formula_str = formula_str.replace('\u00a0', ' ').replace('\u202f', ' ')

    if not formula_str:
        return jsonify({"status": "ERROR", "message": "Formula cannot be empty"}), 400

    MAX_FORMULA_LEN = 2000
    if len(formula_str) > MAX_FORMULA_LEN:
        return jsonify({"status": "ERROR", "message": f"Formula too long (max {MAX_FORMULA_LEN} chars)"}), 400

    mode = data.get("mode", "first")
    if mode not in ("first", "all"):
        mode = "first"

    try:
        # 1. Parse AST
        ast = parse_formula(formula_str)
        variables = sorted(list(get_variables(ast)))

        if not variables:
            return jsonify({"status": "ERROR", "message": "No propositional variables found in formula"}), 400

        if len(variables) > 20:
            return jsonify({"status": "ERROR", "message": f"Too many variables ({len(variables)}). Max is 20."}), 400

        # 2. Convert to CNF
        cnf_formula = ast_to_cnf(ast)
        clauses_str = [str(c) for c in cnf_formula.clauses]

        # Edge case: empty CNF = tautology (always True)
        if not cnf_formula.clauses:
            import itertools
            if mode == "all":
                sol_dicts = [dict(zip(variables, vals)) for vals in itertools.product([True, False], repeat=len(variables))]
            else:
                sol_dicts = [{v: True for v in variables}]
            truth_table = generate_truth_table(ast, set(variables))
            return jsonify({
                "status": "SAT",
                "variables": variables,
                "clauses": ["(Tautology — always True)"],
                "solutions": sol_dicts,
                "steps": [{"type": "success", "assignment": sol_dicts[0]}],
                "truth_table": truth_table
            })

        # 3. Solve
        if mode == "all":
            solutions, steps = solve_all(cnf_formula)
            status = "SAT" if solutions else "UNSAT"
            sol_dicts = [s.to_dict() for s in solutions]
        else:
            first_sol, steps = solve_first(cnf_formula)
            if first_sol:
                status = "SAT"
                sol_dicts = [first_sol.to_dict()]
            else:
                status = "UNSAT"
                sol_dicts = []

        # 4. Generate Truth Table (capped at 8 vars in utils.py)
        truth_table = generate_truth_table(ast, set(variables))

        return jsonify({
            "status": status,
            "variables": variables,
            "clauses": clauses_str,
            "solutions": sol_dicts,
            "steps": steps,
            "truth_table": truth_table
        })

    except SyntaxError as e:
        return jsonify({"status": "ERROR", "message": f"Parse Error: {str(e)}"}), 400
    except RecursionError:
        return jsonify({"status": "ERROR", "message": "Formula is too deeply nested"}), 400
    except Exception as e:
        app.logger.exception("Unexpected error in /api/solve")
        return jsonify({"status": "ERROR", "message": f"Server Error: {str(e)}"}), 500


@app.route("/api/upload-dimacs", methods=["POST"])
def upload_dimacs():
    if "file" not in request.files:
        return jsonify({"status": "ERROR", "message": "No file uploaded"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "ERROR", "message": "Empty filename"}), 400

    mode = request.form.get("mode", "first")

    try:
        content = file.read().decode("utf-8")
        cnf_formula = parse_dimacs(content)
        
        variables = sorted(list(cnf_formula.variables))
        clauses_str = [str(c) for c in cnf_formula.clauses]

        if mode == "all":
            solutions, steps = solve_all(cnf_formula)
            status = "SAT" if solutions else "UNSAT"
            sol_dicts = [s.to_dict() for s in solutions]
        else:
            first_sol, steps = solve_first(cnf_formula)
            if first_sol:
                status = "SAT"
                sol_dicts = [first_sol.to_dict()]
            else:
                status = "UNSAT"
                sol_dicts = []

        return jsonify({
            "status": status,
            "variables": variables,
            "clauses": clauses_str[:100] + (["..."] if len(clauses_str) > 100 else []), # limit output
            "solutions": sol_dicts,
            "steps": steps,
            "truth_table": None # Not generating truth table for DIMACS
        })

    except ValueError as e:
        return jsonify({"status": "ERROR", "message": f"DIMACS Parse Error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Server Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
