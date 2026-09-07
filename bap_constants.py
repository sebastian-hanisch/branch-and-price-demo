"""Defaults, slider bounds und Presets für die Branch-&-Price-Demo."""

DEFAULT_N_TYPES = 4
DEFAULT_MAX_DEMAND = 2
DEFAULT_ROLL_WIDTH = 100
DEFAULT_SEED = 7

N_TYPES_MIN, N_TYPES_MAX = 2, 7
MAX_DEMAND_MIN, MAX_DEMAND_MAX = 1, 4
ROLL_WIDTH_MIN, ROLL_WIDTH_MAX = 50, 200

# Auftragsbreiten werden als Anteil der Rollenbreite gezogen - hält die Instanzen
# unabhängig von der absoluten Rollenbreite vergleichbar (wie in jedem
# vorherigen Stück dieser Linie).
WIDTH_FRACTION_RANGE = (0.15, 0.6)

# Per Prototyp kalibriert (nach Behebung zweier echter Bugs, siehe
# bap_solver.py): 186 Zufallsinstanzen (n_types 2-7, max_demand 1-4) alle
# korrekt und schnell gelöst, größte Instanz < 1,4s. Sicherheitsgrenzen mit
# reichlich Marge.
MAX_BP_NODES = 2000
MAX_CG_ITERATIONS = 200
MAX_NODES_RENDERED = 400
ORTOOLS_TIME_LIMIT_SECONDS = 5.0

PRESETS = {
    "Winzige Instanz (Baum komplett sichtbar)": {
        "n_types": 3, "roll_width": 100, "max_demand": 1, "seed": 1,
    },
    "Mehrere Verzweigungen nötig": {
        "n_types": 5, "roll_width": 100, "max_demand": 3, "seed": 3,
    },
    "Wo die Rundung in column-generation-demo scheiterte": {
        "n_types": 7, "roll_width": 100, "max_demand": 4, "seed": 14,
    },
}
