"""Kennzahlen und der Kernvergleich dieses Stücks: schließt Branch & Price
die Lücke, die column-generation-demo ehrlich offen ließ (eine enge Schranke
ist keine Lösung)?"""

import math
from collections import Counter


def compute_stats(result):
    counts = Counter(node.status for node in result.nodes)
    return {
        "nodes_explored": len(result.nodes),
        "pruned_bound": counts["prune_bound"],
        "leaves_evaluated": counts["leaf_new_best"] + counts["leaf_not_best"],
        "best_value": result.best_value,
        "truncated": result.truncated,
    }


def stats_up_to_step(result, step):
    relevant = [node for node in result.nodes if node.id <= step]
    counts = Counter(node.status for node in relevant)
    current_best = None
    for nid, v in result.incumbent_history:
        if nid <= step:
            current_best = v
    return {
        "nodes_so_far": counts.total(),
        "pruned_bound": counts["prune_bound"],
        "current_best": current_best,
    }


def roundup_vs_exact_comparison(root_obj, root_xs, exact_value, true_optimum):
    """`root_obj`/`root_xs` kommen von bap_solver.root_relaxation. Naives
    Aufrunden wählt jedes Muster mit x_p > 0 einmal (Analogie zu
    column-generation-demos `roundup_bins`, hier auf der 0/1-Mengendeckung
    statt Muster-Mengen - kann Stücke mehrfach abdecken, daher potenziell zu
    viele Rollen)."""
    roundup_bins = sum(1 for x in root_xs if x > 1e-6)
    return {
        "root_lp_bound": root_obj,
        "ceil_root_bound": math.ceil(root_obj - 1e-6),
        "roundup_bins": roundup_bins,
        "exact_value": exact_value,
        "true_optimum": true_optimum,
        "closes_the_gap": exact_value == true_optimum,
    }
