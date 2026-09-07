"""Ruft den echten Google-OR-Tools-CP-SAT-Solver auf derselben Instanz auf -
Standard-Bin-Packing-Modell wie in cutting-stock-constraint-programming-demo,
hier OHNE die dortigen Materialsorten-Constraints. Zusätzlicher, unabhängiger
Korrektheits-Cross-Check für das komplexeste Stück dieser Linie."""

from ortools.sat.python import cp_model

from bap_bruteforce import expand_pieces
from bap_constants import ORTOOLS_TIME_LIMIT_SECONDS


def solve_with_ortools(instance, time_limit_seconds=ORTOOLS_TIME_LIMIT_SECONDS):
    pieces = expand_pieces(instance)
    n = len(pieces)
    max_bins = n

    model = cp_model.CpModel()
    x = [[model.NewBoolVar(f"x{i}_{k}") for k in range(max_bins)] for i in range(n)]
    y = [model.NewBoolVar(f"y{k}") for k in range(max_bins)]

    for i in range(n):
        model.Add(sum(x[i][k] for k in range(max_bins)) == 1)
    for k in range(max_bins):
        model.Add(sum(pieces[i] * x[i][k] for i in range(n)) <= instance.roll_width * y[k])

    model.Minimize(sum(y))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 1

    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        best_value = int(round(solver.ObjectiveValue()))
    else:
        best_value = None

    return {
        "status": solver.StatusName(status),
        "proven_optimal": status == cp_model.OPTIMAL,
        "best_value": best_value,
        "wall_time": solver.WallTime(),
    }
