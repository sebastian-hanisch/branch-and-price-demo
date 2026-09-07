"""
Branch-and-Price am Cutting-Stock-Problem – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes und LETZTES Stück der Cutting-Stock-Linie: die Konvergenz von
Verzweigung und Spaltengenerierung, mit echter Ryan-Foster-Verzweigung.
Direkter Aufhänger: column-generation-demo endete mit dem ehrlichen
Cliffhanger "eine enge Schranke ist keine Lösung" - dieses Stück löst genau
das exakt.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import bap_constants as C
from bap_bruteforce import solve_bruteforce
from bap_evaluation import roundup_vs_exact_comparison, stats_up_to_step
from bap_ortools_reference import solve_with_ortools
from bap_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from bap_scenario import generate_instance
from bap_solver import root_relaxation, solve
from bap_visualization import build_gap_comparison_chart, build_tree_figure

st.set_page_config(page_title="Branch-and-Price am Cutting-Stock-Problem – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_solve(n_types, roll_width, max_demand, seed):
    instance = generate_instance(n_types, roll_width, max_demand, seed)
    result = solve(instance)
    true_optimum = solve_bruteforce(instance)
    return instance, result, true_optimum


@st.cache_data(show_spinner=False)
def _compute_comparison(n_types, roll_width, max_demand, seed, exact_value, true_optimum):
    instance = generate_instance(n_types, roll_width, max_demand, seed)
    root_obj, root_xs, _ = root_relaxation(instance)
    cmp = roundup_vs_exact_comparison(root_obj, root_xs, exact_value, true_optimum)
    ortools_result = solve_with_ortools(instance)
    cmp["ortools_best_value"] = ortools_result["best_value"]
    cmp["ortools_proven_optimal"] = ortools_result["proven_optimal"]
    return cmp


st.title("🌳📐 Branch-and-Price am Cutting-Stock-Problem")
st.markdown(
    """
Siebtes und **letztes** Stück der Cutting-Stock-Linie - die Konvergenz von
Verzweigung und Spaltengenerierung, mit ECHTER Ryan-Foster-Verzweigung (nicht
naiver Verzweigung auf einer Muster-Variable, die strukturell nicht sauber
funktioniert). Direkter Aufhänger:
[column-generation-demo](https://github.com/sebastian-hanisch/column-generation-demo)
endete mit dem ehrlichen Cliffhanger "eine enge Schranke ist keine Lösung" -
naives Aufrunden traf das Optimum nur in ~55 % der Fälle. Dieses Stück löst
genau das exakt.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren "
    "vergleichen, zeigt diese Demo - wie jedes Stück dieser Linie - ein Verfahren an einem "
    "wachsenden Beispiel."
)

with st.expander("So funktioniert Ryan-Foster-Verzweigung", expanded=True):
    st.markdown(
        r"""
Bei einer fraktionalen Lösung wird das fraktionalste Stückpaar (i, j) aus
**unterschiedlichen** Auftragstypen gesucht (gleiche Typen sind austauschbar,
eine Verzweigung darauf wäre reine Verschwendung - siehe
`cutting-stock-cutting-planes-demo`). Zwei Kinder:

- **ZUSAMMEN**: jedes künftige Muster enthält entweder BEIDE Stücke oder KEINES.
- **GETRENNT**: kein künftiges Muster darf BEIDE Stücke enthalten.

Das wirkt direkt im Pricing-Teilproblem - diesmal ein BESCHRÄNKTER Rucksack
(jedes Stück höchstens einmal verwendbar), gelöst per rekursivem Branch &
Bound über die Stücke: ein direkter Rückgriff auf `branch-bound-demo`, das
allererste Stück der ganzen Konzepte-Reihe.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Winzige Instanz (Baum komplett sichtbar)": "3 Auftragstypen - der komplette Branch-and-Price-Baum passt aufs Bild.",
    "Mehrere Verzweigungen nötig": "Mehrere Ryan-Foster-Entscheidungen nötig, bis die Lösung ganzzahlig wird.",
    "Wo die Rundung in column-generation-demo scheiterte": "Genau die Instanz, bei der naives Aufrunden dort 9 statt 6 Rollen lieferte - hier exakt gelöst.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_types = st.slider("Anzahl Auftragstypen", *bounds("n_types_slider"), key="n_types_slider")
    roll_width = st.slider("Rollenbreite", *bounds("roll_width_slider"), key="roll_width_slider")
    max_demand = st.slider(
        "Maximaler Bedarf je Auftragstyp", *bounds("max_demand_slider"), key="max_demand_slider",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        use_container_width=True,
        on_click=randomize_seed,
        help="Würfelt neue Auftragsbreiten und -mengen.",
    )

sync_query_params(n_types, roll_width, max_demand, seed)

scenario_key = (int(n_types), int(roll_width), int(max_demand), int(seed))

with st.spinner("Durchsuche den Branch-and-Price-Baum..."):
    instance, result, true_optimum = _compute_solve(*scenario_key)

st.caption(
    f"🔗 {instance.n_types} Auftragstypen, Breiten {instance.item_widths} mit Bedarf "
    f"{instance.item_demands}, Rollenbreite {instance.roll_width}."
)

st.markdown("## 🎯 Der Branch-and-Price-Baum")

if "bap_step" not in st.session_state or st.session_state.get("bap_step_owner") != scenario_key:
    st.session_state["bap_step"] = len(result.nodes) - 1
    st.session_state["bap_step_owner"] = scenario_key

max_step = len(result.nodes) - 1
if max_step == 0:
    step = 0
    st.caption("Schon die Wurzel war ganzzahlig - kein Regler nötig.")
else:
    step = st.slider(
        "Schritt (Knoten)", 0, max_step, key="bap_step",
        help="Ein Schritt = ein Branch-and-Price-Knoten (eigene Spaltengenerierung).",
    )

render_note = (
    f" (zeigt die ersten {C.MAX_NODES_RENDERED:,} von {len(result.nodes):,} Knoten)"
    if len(result.nodes) > C.MAX_NODES_RENDERED
    else ""
)
st.caption(f"{len(result.nodes):,} Knoten insgesamt besucht{render_note}.")

st.plotly_chart(build_tree_figure(result, step, C.MAX_NODES_RENDERED), use_container_width=True, key=f"tree_{step}")

live = stats_up_to_step(result, step)
lm1, lm2, lm3 = st.columns(3)
lm1.metric("Besuchte Knoten (bisher)", f"{live['nodes_so_far']:,}")
lm2.metric(
    "Gestutzt (Bound)", f"{live['pruned_bound']:,}",
    help="Knoten, deren Spaltengenerierungs-Schranke keine Verbesserung mehr versprach.",
)
lm3.metric(
    "Bester Fund bisher", live["current_best"] if live["current_best"] is not None else "–",
    help="Die wenigsten Rollen einer bislang gefundenen ganzzahligen Lösung.",
)

if result.truncated:
    st.error(
        f"⛔ Abgebrochen bei {C.MAX_BP_NODES:,} untersuchten Knoten - das gezeigte Ergebnis ist die "
        f"beste bislang gefundene, nicht garantiert optimale Lösung."
    )
else:
    st.caption(
        f"Bewiesenes Optimum: **{result.best_value}** Rollen - stimmt mit der unabhängigen "
        f"Bruteforce-Referenz überein."
        if result.best_value == true_optimum
        else f"⚠️ Optimum {result.best_value} weicht von der Bruteforce-Referenz {true_optimum} ab - bitte melden."
    )

st.markdown("---")

st.subheader("📐 Schließt sich die Lücke zur echten Lösung?")
st.markdown(
    """
Live für Ihre aktuelle Instanz: naives Aufrunden der Wurzel-Spaltengenerierung
gegen das exakte Ergebnis dieses Stücks - plus der echte OR-Tools-CP-SAT-Solver
als unabhängiger Beleg.

**Warum die Rundungs-Zahl hier oft schlechter aussieht als bei
`column-generation-demo`s eigenem Cliffhanger, selbst bei identischer
Instanz**: dort deckte die LP-Relaxation Auftragstyp-*Mengen* ab (wenige,
großzügige Muster), hier deckt sie einzelne *Stücke* ab (Voraussetzung für
echte Ryan-Foster-Verzweigung) - das verteilt sich typischerweise auf
deutlich mehr, kleinteiligere fraktionale Muster, die naives Aufrunden noch
verschwenderischer macht. Eine noch stärkere, nicht schwächere Illustration
desselben Punkts: eine bloß andere LP-Formulierung ersetzt echte Verzweigung
nicht - erst die Ryan-Foster-Verzweigung schließt die Lücke zuverlässig.
"""
)

cmp = _compute_comparison(*scenario_key, result.best_value, true_optimum)
st.plotly_chart(build_gap_comparison_chart(cmp), use_container_width=True, key="gap_comparison")

gc1, gc2, gc3 = st.columns(3)
gc1.metric("Naives Aufrunden", f"{cmp['roundup_bins']} Rollen", help=f"Wurzel-LP-Schranke: {cmp['root_lp_bound']:.3f}")
gc2.metric("Branch-and-Price (exakt)", f"{cmp['exact_value']} Rollen")
gc3.metric(
    "OR-Tools CP-SAT", cmp["ortools_best_value"],
    help="beweist Optimalität." if cmp["ortools_proven_optimal"] else "Zeitlimit erreicht.",
)

if cmp["closes_the_gap"] and cmp["exact_value"] == cmp["ortools_best_value"]:
    if cmp["roundup_bins"] > cmp["exact_value"]:
        st.success(
            f"✅ Naives Aufrunden hätte hier **{cmp['roundup_bins']}** Rollen gebraucht - "
            f"Branch-and-Price findet das tatsächliche Optimum von **{cmp['exact_value']}** Rollen, "
            f"bestätigt durch OR-Tools und die Bruteforce-Referenz."
        )
    else:
        st.info(
            "Bei dieser Instanz trifft sogar naives Aufrunden bereits das Optimum - probieren Sie das "
            "Preset \"Wo die Rundung in column-generation-demo scheiterte\" für den Gegensatz."
        )
else:
    st.warning("⚠️ Die Verfahren sind sich uneinig - das sollte nie passieren, bitte melden.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Ryan-Foster SAME/DIFFER**: bei einer fraktionalen Lösung existiert
nachweislich (Mengendeckungs-Theorie) ein Stückpaar (i, j), dessen
gemeinsames Vorkommen $y_{ij} = \sum_{p:\ i,j \in p} x_p$ fraktional ist.
"ZUSAMMEN" verbietet künftig jedes Muster mit GENAU einem der beiden Stücke;
"GETRENNT" verbietet jedes Muster mit BEIDEN. Beide Zweige schließen die
aktuelle fraktionale Lösung aus - der Suchbaum macht garantiert Fortschritt.

**Entartung beim Pricing**: Spaltengenerierungs-LPs sind häufig entartet
(mehrere Dual-Lösungen mit demselben Zielfunktionswert) - naives Pricing
kann dadurch IMMER WIEDER dasselbe, bereits bekannte Muster liefern und
fälschlich "keine Verbesserung mehr möglich" schließen, obwohl die
Spaltengenerierung noch nicht am Ende ist. Deshalb sucht das Pricing hier
gezielt nach dem besten NOCH NICHT bekannten Muster - das garantiert bei
jedem Aufruf echten Fortschritt, unabhängig davon, welche Dual-Lösung die
LP gerade liefert.

**Abschneide-Bedingung**: ein Knoten wird verworfen, sobald seine
aufgerundete Spaltengenerierungs-Schranke ($\lceil \text{LP-Schranke}
\rceil$) das bislang beste gefundene Ergebnis nicht mehr unterbieten kann -
dieselbe Branch-and-Bound-Logik wie in `branch-bound-demo`, hier auf eine
per Spaltengenerierung gelöste statt einer einfachen LP-Schranke
angewendet.

**Warum das jetzt tatsächlich funktioniert, wo `column-generation-demo`
ehrlich scheiterte**: dort wurde die fraktionale LP-Lösung nur EINMAL naiv
gerundet. Hier wird bei jeder fraktionalen Lösung GEZIELT verzweigt, bis eine
ganzzahlige Lösung erreicht ist - mit Kind-Knoten, die ihre Spaltengenerierung
aus den (gefilterten) Mustern des Elternknotens warmstarten, statt bei null
zu beginnen.

Implementiert in `bap_pricing.py` (Pricing mit Degenerations-Fix),
`bap_master.py` (Mengendeckungs-LP), `bap_solver.py` (Branch-and-Price-Baum
mit Warmstart und korrektem Abschneiden) und `bap_bruteforce.py`/
`bap_ortools_reference.py` (unabhängige Referenzlösungen).
        """
    )

st.markdown("---")

st.markdown("## 🏁 Die ganze Cutting-Stock-Linie im Rückblick")
st.markdown(
    """
Mit diesem siebten Stück ist die Linie vollständig - hier der ganze Bogen
vom ersten bis zum letzten Stück:

**Start - reine Suche, eine Schwäche bewusst offen gelassen**:
[cutting-stock-branch-bound-demo](https://github.com/sebastian-hanisch/cutting-stock-branch-bound-demo)
verzweigt über Bin-Zuweisungen, lässt austauschbare (symmetrische) Bins aber
absichtlich unbehandelt - der Suchbaum bläht sich dadurch unnötig auf.

**Zwei unabhängige Antworten auf diese Wurzel**:
[cutting-stock-dp-demo](https://github.com/sebastian-hanisch/cutting-stock-dp-demo)
tabelliert über Bedarfsvektoren statt zu verzweigen - derselbe Suchraum,
andere Darstellung, mit einem eigenen, andersartigen Nachteil (der
Zustandsraum wächst mit der Anzahl Auftragstypen, nicht mit der
Rollenbreite).
[cutting-stock-cutting-planes-demo](https://github.com/sebastian-hanisch/cutting-stock-cutting-planes-demo)
behebt die Symmetrie tatsächlich, statt sie nur zu zeigen: ein echter
algorithmischer Schnitt, der baugleiche offene Bins gar nicht erst als
eigene Äste erzeugt.

**Erste Konvergenz**:
[cutting-stock-branch-cut-demo](https://github.com/sebastian-hanisch/cutting-stock-branch-cut-demo)
kombiniert die Verzweigung der Wurzel mit dem Symmetrie-Schnitt UND einer an
jedem Knoten frisch gelösten LP-Schranke - echtes, per Knoten wiederholtes
Branch & Cut, näher an dem, was reale Solver einsetzen, als jedes
Einzelverfahren.

**Ein unabhängiger Zweig**:
[cutting-stock-constraint-programming-demo](https://github.com/sebastian-hanisch/cutting-stock-constraint-programming-demo)
verlässt Schranken-Vergleiche ganz zugunsten von Constraint-Propagation, für
eine echte Materialsorten-Nebenbedingung, die eine LP-Schranke gar nicht
ausdrücken könnte.

**Der eigentliche Anlass dieser Linie**:
[column-generation-demo](https://github.com/sebastian-hanisch/column-generation-demo)
verlässt die Suche komplett - ein Master-LP fordert gezielt neue
Schnittmuster an, statt vorab exponentiell viele durchzuprobieren. Die
Schranke ist dabei bemerkenswert eng, aber das allein reicht nicht: naives
Aufrunden der fraktionalen Lösung trifft das Optimum nur in etwa der Hälfte
der Fälle.

**Zweite Konvergenz - dieses Stück** schließt genau diese Lücke: echte
Ryan-Foster-Verzweigung erzwingt bei jeder fraktionalen Lösung gezielt zwei
Stücke zusammen oder getrennt, kombiniert mit Spaltengenerierung an jedem
Knoten - ein direkter Rückgriff auf sowohl `column-generation-demo` (die
Spaltengenerierung selbst) als auch `cutting-stock-branch-bound-demo` (das
Pricing-Teilproblem ist wieder ein Rucksack, gelöst mit demselben
rekursiven Branch & Bound wie ganz am Anfang der gesamten Konzepte-Reihe).

**Die übergeordnete Lektion**: exakte Suche ist kein einzelnes Verfahren,
sondern ein Spektrum zwischen zwei Polen - reine Baumsuche mit Schranken
(Branch & Bound, Branch & Cut) auf der einen, LP-basierte Verfahren mit
exponentiell vielen impliziten Variablen (Column Generation) auf der
anderen Seite. Branch-and-Price kombiniert genau diese beiden Pole - und
ist in der Praxis tatsächlich das Standardverfahren, mit dem reale Solver
Tourenplanung, Personaleinsatzplanung und Zuschnittoptimierung in
industriellem Maßstab lösen.

Derselbe methodische Bogen wie die erste (Rucksack-)Linie - nur mit zwei
zusätzlichen Stücken, die reines Rucksack strukturell nicht hergab: ein
Problem mit natürlich exponentiell vielen impliziten Variablen
(Schnittmustern) ist genau das, was Column Generation und Branch-and-Price
brauchen.
"""
)

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
