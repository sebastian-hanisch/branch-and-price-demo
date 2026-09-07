"""Erschöpfende Bin-Packing-Referenzlösung - unabhängig von Branch & Price,
nur für kleine Instanzen praktikabel. Wie in jedem vorherigen Stück dieser
Linie: Bedarfsmengen zu Einzelstücken expandiert, absteigend sortiert,
höchstens ein neues Bin pro Schritt durchprobiert."""


def expand_pieces(instance):
    pieces = []
    for w, q in zip(instance.item_widths, instance.item_demands):
        pieces.extend([w] * q)
    pieces.sort(reverse=True)
    return tuple(pieces)


def solve_bruteforce(instance):
    pieces = expand_pieces(instance)
    n = len(pieces)
    best = {"count": n}  # triviale obere Schranke: ein Bin pro Stück

    def assign(idx, bins):
        if len(bins) >= best["count"]:
            return
        if idx == n:
            best["count"] = min(best["count"], len(bins))
            return
        piece = pieces[idx]
        for i, cap in enumerate(bins):
            if cap >= piece:
                bins[i] -= piece
                assign(idx + 1, bins)
                bins[i] += piece
        bins.append(instance.roll_width - piece)
        assign(idx + 1, bins)
        bins.pop()

    assign(0, [])
    return best["count"]
