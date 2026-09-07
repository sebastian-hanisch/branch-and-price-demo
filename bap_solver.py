"""Branch-and-Price: an jedem Suchbaum-Knoten wird eine eigene Spalten-
generierung gelöst (Muster vom Elternknoten geerbt und auf Zulässigkeit
gefiltert - Standardpraxis in echtem Branch-and-Price, hier bewusst zuerst
ohne Vererbung implementiert und dann als klar messbarer Geschwindigkeits-
gewinn nachgewiesen); bei einer fraktionalen Lösung wird per echter
Ryan-Foster-Regel verzweigt (SAME/DIFFER auf dem fraktionalsten Stückpaar
UNTERSCHIEDLICHER Auftragstypen), nicht naiv auf einer Muster-Variable.

Status-Vokabular wie in branch-bound-demo (root/branch/prune_bound/
leaf_new_best/leaf_not_best), aber BINÄR statt n-är - jede Verzweigung hat
genau zwei Kinder (ZUSAMMEN/GETRENNT)."""

import math
from dataclasses import dataclass

from bap_constants import MAX_BP_NODES, MAX_CG_ITERATIONS
from bap_master import solve_master
from bap_pricing import price_pattern
from bap_scenario import expand_pieces_with_types


@dataclass(frozen=True)
class Node:
    id: int
    parent_id: object
    depth: int
    decision: object  # "same" | "differ" | None (Wurzel)
    branch_types: object  # (Auftragstyp A, Auftragstyp B) der Verzweigung, die zu diesem Knoten führte - None für die Wurzel
    bound: object  # LP-Zielfunktionswert an diesem Knoten (Spaltengenerierungs-Ergebnis)
    status: str  # root | branch | prune_bound | leaf_new_best | leaf_not_best
    n_patterns: int


@dataclass(frozen=True)
class SolveResult:
    best_value: object
    best_patterns: tuple  # gewählte Muster (Frozensets von Stück-Indizes) der besten Lösung
    nodes: tuple
    incumbent_history: tuple
    truncated: bool
    pieces: tuple  # (Breite, Auftragstyp) je Einzelstück


def _pattern_respects_constraints(pattern, same_pairs, differ_pairs):
    for a, b in same_pairs:
        if (a in pattern) != (b in pattern):
            return False
    for a, b in differ_pairs:
        if a in pattern and b in pattern:
            return False
    return True


def _initial_patterns(pieces, capacity, same_pairs, differ_pairs):
    """Ein Muster pro Stück allein (SAME-Partner transitiv mit aufgenommen) -
    garantiert von Anfang an ein zulässiges Master-LP."""
    n = len(pieces)
    patterns = []
    seen = set()
    for i in range(n):
        base = {i}
        changed = True
        while changed:
            changed = False
            for a, b in same_pairs:
                if a in base and b not in base:
                    base.add(b)
                    changed = True
                elif b in base and a not in base:
                    base.add(a)
                    changed = True
        total_w = sum(pieces[j][0] for j in base)
        frozen = frozenset(base)
        if total_w <= capacity and frozen not in seen:
            seen.add(frozen)
            patterns.append(frozen)
    return patterns


def _column_generation_at_node(pieces, capacity, same_pairs, differ_pairs, initial_patterns, max_iter=MAX_CG_ITERATIONS):
    n = len(pieces)
    patterns = list(initial_patterns)
    known = set(patterns)
    for _ in range(max_iter):
        obj, xs, duals = solve_master(n, patterns)
        if obj is None:
            return None, None, patterns  # unzulässiger Knoten
        best_val, chosen = price_pattern(pieces, duals, capacity, same_pairs, differ_pairs, known_patterns=known)
        reduced_cost = 1 - best_val
        if reduced_cost < -1e-6 and chosen:
            patterns.append(chosen)
            known.add(chosen)
        else:
            return obj, xs, patterns
    return obj, xs, patterns


def _find_branch_pair(pieces, xs, patterns):
    """Fraktionalstes Stückpaar UNTERSCHIEDLICHER Auftragstypen (am nächsten
    an 0,5) - gleiche Typen sind austauschbar, ein Rückgriff auf die
    Symmetrie-Lektion aus cutting-stock-cutting-planes-demo. Standardpraxis:
    das fraktionalste statt das erstbeste Paar wählen (per Prototyp verankert
    - deutlich kleinere Bäume als bei willkürlicher Paarwahl)."""
    candidates = {}
    for p_idx, pat in enumerate(patterns):
        xv = xs[p_idx]
        if xv <= 1e-6 or xv >= 1 - 1e-6:
            continue
        pat_list = list(pat)
        for a_idx in range(len(pat_list)):
            for b_idx in range(a_idx + 1, len(pat_list)):
                i, j = pat_list[a_idx], pat_list[b_idx]
                if pieces[i][1] == pieces[j][1]:
                    continue
                key = (min(i, j), max(i, j))
                candidates[key] = candidates.get(key, 0.0) + xv
    best_pair, best_dist = None, 1.0
    for (i, j), y in candidates.items():
        if 1e-6 < y < 1 - 1e-6:
            dist = abs(y - 0.5)
            if dist < best_dist:
                best_dist = dist
                best_pair = (i, j)
    return best_pair


def _is_integral(xs):
    return all(x <= 1e-6 or x >= 1 - 1e-6 for x in xs)


@dataclass
class _StackEntry:
    parent_id: object
    depth: int
    decision: object
    branch_types: object
    same_pairs: tuple
    differ_pairs: tuple
    inherited_patterns: tuple


def root_relaxation(instance):
    """Das Wurzel-LP (keine SAME/DIFFER-Constraints) - für den Vergleich
    "naives Aufrunden vs. exaktes Ergebnis" in bap_evaluation.py. Gibt
    (Zielfunktionswert, x-Werte, Muster) zurück."""
    pieces = expand_pieces_with_types(instance)
    capacity = instance.roll_width
    init_pats = _initial_patterns(pieces, capacity, (), ())
    return _column_generation_at_node(pieces, capacity, (), (), init_pats)


def solve(instance, max_nodes=MAX_BP_NODES):
    pieces = expand_pieces_with_types(instance)
    capacity = instance.roll_width

    nodes = []
    incumbent_history = []
    best = {"value": None, "patterns": None}
    truncated = {"flag": False}
    next_id = [0]

    stack = [_StackEntry(None, 0, None, None, (), (), ())]

    while stack:
        if next_id[0] >= max_nodes:
            truncated["flag"] = True
            break
        entry = stack.pop()

        inherited = [p for p in entry.inherited_patterns if _pattern_respects_constraints(p, entry.same_pairs, entry.differ_pairs)]
        base_pats = _initial_patterns(pieces, capacity, entry.same_pairs, entry.differ_pairs)
        seen = set()
        init_pats = []
        for p in inherited + base_pats:
            if p not in seen:
                seen.add(p)
                init_pats.append(p)

        obj, xs, patterns = _column_generation_at_node(pieces, capacity, entry.same_pairs, entry.differ_pairs, init_pats)

        node_id = next_id[0]
        next_id[0] += 1

        if obj is None:
            continue  # unzulässiger Knoten - kein Eintrag im Baum (analog zu strukturell nie erzeugten Optionen anderswo in dieser Linie)

        status = "root" if entry.parent_id is None else "branch"

        if best["value"] is not None and math.ceil(obj - 1e-6) >= best["value"]:
            nodes.append(Node(node_id, entry.parent_id, entry.depth, entry.decision, entry.branch_types, obj, "prune_bound", len(patterns)))
            continue

        if _is_integral(xs):
            value = sum(round(x) for x in xs)
            is_new_best = best["value"] is None or value < best["value"]
            leaf_status = "leaf_new_best" if is_new_best else "leaf_not_best"
            nodes.append(Node(node_id, entry.parent_id, entry.depth, entry.decision, entry.branch_types, obj, leaf_status, len(patterns)))
            if is_new_best:
                best["value"] = value
                best["patterns"] = [p for p, x in zip(patterns, xs) if round(x) == 1]
                incumbent_history.append((node_id, value))
            continue

        pair = _find_branch_pair(pieces, xs, patterns)
        if pair is None:
            # Fallback: irgendein fraktionales Paar (auch gleicher Typ) - selten,
            # aber die Suche muss trotzdem terminieren können.
            for p_idx, pat in enumerate(patterns):
                if 1e-6 < xs[p_idx] < 1 - 1e-6:
                    pat_list = list(pat)
                    if len(pat_list) >= 2:
                        pair = (pat_list[0], pat_list[1])
                        break
        if pair is None:
            nodes.append(Node(node_id, entry.parent_id, entry.depth, entry.decision, entry.branch_types, obj, "leaf_not_best", len(patterns)))
            continue

        nodes.append(Node(node_id, entry.parent_id, entry.depth, entry.decision, entry.branch_types, obj, status, len(patterns)))

        i, j = pair
        pair_types = (pieces[i][1], pieces[j][1])
        stack.append(_StackEntry(node_id, entry.depth + 1, "same", pair_types, entry.same_pairs + ((i, j),), entry.differ_pairs, tuple(patterns)))
        stack.append(_StackEntry(node_id, entry.depth + 1, "differ", pair_types, entry.same_pairs, entry.differ_pairs + ((i, j),), tuple(patterns)))

    return SolveResult(
        best_value=best["value"],
        best_patterns=tuple(best["patterns"]) if best["patterns"] is not None else (),
        nodes=tuple(nodes),
        incumbent_history=tuple(incumbent_history),
        truncated=truncated["flag"],
        pieces=tuple(pieces),
    )
