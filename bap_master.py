"""Das Mengendeckungs-LP über einzelne Stücke - analog zu
column-generation-demo/cg_master.py, aber mit `bounds=(0,1)` statt `(0,None)`:
jedes Muster wird höchstens einmal verwendet (0/1-Semantik), weil einzelne
Stücke - anders als Auftragstyp-Mengen - nicht beliebig oft wiederholt werden
können."""

import numpy as np
from scipy.optimize import linprog


def solve_master(n_pieces, patterns):
    """patterns: Liste von Frozensets (Stück-Indizes je Muster). Minimiere
    sum(x_p) unter sum_p(1[i in p] * x_p) >= 1 für jedes Stück i,
    0 <= x_p <= 1.

    Wie in column-generation-demo: scipy kennt nur <=, die Deckungsbedingung
    wird negiert (-sum_p(...) <= -1); die zurückgegebenen Dual-Werte werden
    negiert, damit sie als nicht-negative Pricing-Werte nutzbar sind."""
    n_patterns = len(patterns)
    c = np.ones(n_patterns)
    A_ub = np.zeros((n_pieces, n_patterns))
    for p_idx, pattern in enumerate(patterns):
        for i in pattern:
            A_ub[i, p_idx] = -1.0
    b_ub = np.full(n_pieces, -1.0)
    bounds = [(0, 1)] * n_patterns

    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    if not result.success:
        return None, None, None
    duals = -result.ineqlin.marginals
    return result.fun, result.x, duals
