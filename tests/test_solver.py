import pytest

from bap_bruteforce import solve_bruteforce
from bap_constants import PRESETS
from bap_ortools_reference import solve_with_ortools
from bap_scenario import CuttingStockInstance, generate_instance
from bap_solver import solve


def test_matches_hand_computed_example():
    instance = CuttingStockInstance(roll_width=10, item_widths=(6,), item_demands=(3,))
    result = solve(instance)
    assert result.best_value == 3
    assert solve_bruteforce(instance) == 3


def test_matches_bruteforce_across_random_small_instances():
    for n_types in range(2, 5):
        for max_demand in range(1, 4):
            for seed in range(10):
                instance = generate_instance(n_types, 100, max_demand, seed)
                result = solve(instance, max_nodes=500)
                assert not result.truncated, f"n={n_types} d={max_demand} seed={seed}"
                true_min = solve_bruteforce(instance)
                assert result.best_value == true_min, f"n={n_types} d={max_demand} seed={seed}"


def test_matches_bruteforce_on_larger_instances():
    for n_types in range(4, 8):
        for max_demand in range(2, 5):
            for seed in range(6):
                instance = generate_instance(n_types, 100, max_demand, seed)
                result = solve(instance, max_nodes=2000)
                if result.truncated:
                    continue
                true_min = solve_bruteforce(instance)
                assert result.best_value == true_min, f"n={n_types} d={max_demand} seed={seed}"


def test_bug1_regression_pricing_no_longer_stops_on_degenerate_duals():
    # Vor dem Fix (Pricing suchte nicht explizit nach dem besten NOCH NICHT
    # bekannten Muster) lieferte diese Instanz die ungültige Schranke 4.0
    # statt korrekt 3.0 - eine entartete Spaltengenerierungs-Schleife fand
    # immer wieder dasselbe bereits bekannte Muster und brach fälschlich ab.
    instance = generate_instance(n_types=4, roll_width=100, max_demand=2, seed=1)
    result = solve(instance, max_nodes=500)
    assert not result.truncated
    assert result.best_value == solve_bruteforce(instance) == 3


def test_bug2_regression_pruning_terminates_quickly():
    # Vor dem Fix (verschachtelte, fehlerhafte Abschneide-Bedingung)
    # explodierte diese Instanz auf >1000 Knoten ohne je eine Lösung zu
    # finden. Nach dem Fix: deutlich unter 100 Knoten.
    instance = generate_instance(n_types=6, roll_width=100, max_demand=3, seed=0)
    result = solve(instance, max_nodes=500)
    assert not result.truncated
    assert len(result.nodes) < 100
    assert result.best_value == solve_bruteforce(instance)


def test_closes_the_gap_where_column_generation_demos_roundup_failed():
    # Der konkrete, cross-repo verifizierte Beweis: column-generation-demo
    # rundete auf dieser exakten Instanz (n=7, d=4, seed=14) fälschlich auf 9
    # Rollen auf, obwohl das wahre Optimum 6 ist. Dieses Stück muss die
    # exakte 6 liefern.
    instance = generate_instance(n_types=7, roll_width=100, max_demand=4, seed=14)
    result = solve(instance, max_nodes=2000)
    assert not result.truncated
    assert result.best_value == 6
    assert result.best_value == solve_bruteforce(instance)


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_presets_solve_correctly(name):
    instance = generate_instance(**PRESETS[name])
    result = solve(instance, max_nodes=2000)
    assert not result.truncated
    true_min = solve_bruteforce(instance)
    assert result.best_value == true_min, name


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_presets_match_ortools_cross_check(name):
    instance = generate_instance(**PRESETS[name])
    result = solve(instance, max_nodes=2000)
    ortools_result = solve_with_ortools(instance, time_limit_seconds=10.0)
    assert ortools_result["best_value"] == result.best_value, name


def test_max_nodes_cap_is_honored_and_flagged_as_truncated():
    # n=5/d=3/seed=3 braucht per Prototyp bekanntermaßen 29 Knoten - eine
    # Grenze von 3 muss dieselbe Instanz zuverlässig abbrechen.
    instance = generate_instance(n_types=5, roll_width=100, max_demand=3, seed=3)
    result = solve(instance, max_nodes=3)
    assert result.truncated
