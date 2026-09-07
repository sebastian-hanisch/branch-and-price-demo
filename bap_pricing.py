"""Das Pricing-Teilproblem: ein 0/1-Rucksack über einzelne Stücke (jedes Stück
höchstens einmal - anders als column-generation-demos UNBESCHRÄNKTE Variante,
da hier physische Einzelstücke statt Auftragstyp-Mengen betrachtet werden),
das aktive SAME-Constraints (beide rein oder beide raus) und DIFFER-
Constraints (höchstens eines der beiden) respektiert. Gelöst per rekursivem
Branch & Bound über die Stücke - ein direkter Rückgriff auf branch-bound-demo,
das allererste Stück der ganzen Konzepte-Reihe, jetzt eine Zutat im letzten
Stück dieser Linie."""


def price_pattern(pieces, values, capacity, same_pairs, differ_pairs, known_patterns=frozenset()):
    """`pieces`: Liste (Breite, Auftragstyp). `values`: Dual-Wert je Stück.
    `same_pairs`/`differ_pairs`: Tupel von (Stück-Index, Stück-Index).
    `known_patterns`: bereits im Master vorhandene Muster (als Frozensets von
    Stück-Indizes).

    Spaltengenerierungs-LPs sind häufig ENTARTET (mehrere Dual-Lösungen mit
    demselben Zielfunktionswert) - naives erneutes Pricing kann dadurch
    IMMER WIEDER dasselbe, bereits bekannte Muster liefern und fälschlich
    "keine Verbesserung mehr möglich" schließen, obwohl das echte LP-Optimum
    noch nicht erreicht ist. Per Prototyp konkret nachgewiesen (eine Instanz
    lieferte dadurch eine ungültige, zu hohe Schranke: 4.0 statt korrekt
    3.0). Fix: die Suche wird angewiesen, das beste NOCH NICHT bekannte
    Muster zu finden, statt einfach das global beste - fällt das global beste
    zufällig mit einem bekannten Muster zusammen, sucht die Suche gezielt
    nach der besten echten Alternative weiter.

    Gibt (bester Wert, Frozenset gewählter Stück-Indizes) zurück."""
    n = len(pieces)
    order = sorted(range(n), key=lambda i: -values[i] / max(1, pieces[i][0]))
    widths = [pieces[i][0] for i in order]
    vals = [values[i] for i in order]
    suffix_max = [0.0] * (n + 1)
    for k in range(n - 1, -1, -1):
        suffix_max[k] = suffix_max[k + 1] + max(0.0, vals[k])

    best = {"value": 0.0, "chosen": frozenset()}

    def conflicts_with(chosen, idx_orig):
        for a, b in differ_pairs:
            if idx_orig == a and b in chosen:
                return True
            if idx_orig == b and a in chosen:
                return True
        return False

    def same_violation(chosen, excluded, idx_orig, include):
        for a, b in same_pairs:
            other = b if idx_orig == a else (a if idx_orig == b else None)
            if other is None:
                continue
            if include and other in excluded:
                return True
            if not include and other in chosen:
                return True
        return False

    def recurse(pos, remaining_cap, chosen, excluded, value):
        if value + suffix_max[pos] <= best["value"] + 1e-9:
            return
        if pos == n:
            if value > best["value"] + 1e-9 and frozenset(chosen) not in known_patterns:
                best["value"] = value
                best["chosen"] = frozenset(chosen)
            return
        idx_orig = order[pos]
        w = widths[pos]
        v = vals[pos]

        if w <= remaining_cap and not conflicts_with(chosen, idx_orig) and not same_violation(chosen, excluded, idx_orig, True):
            recurse(pos + 1, remaining_cap - w, chosen | {idx_orig}, excluded, value + v)
        if not same_violation(chosen, excluded, idx_orig, False):
            recurse(pos + 1, remaining_cap, chosen, excluded | {idx_orig}, value)

    recurse(0, capacity, frozenset(), frozenset(), 0.0)
    return best["value"], best["chosen"]
