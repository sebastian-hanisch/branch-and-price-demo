# Branch & Price am Cutting-Stock-Problem – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-branch-and-price-demo.streamlit.app/)**

Siebtes und **letztes** Stück der Cutting-Stock-Linie - die Konvergenz von
Verzweigung und Spaltengenerierung, mit ECHTER Ryan-Foster-Verzweigung (nicht
naiver Verzweigung auf einer Muster-Variable, die strukturell nicht sauber
funktioniert - so seit Beginn dieser Linie festgehalten). Direkter Aufhänger:
[column-generation-demo](https://github.com/sebastian-hanisch/column-generation-demo)
endete mit dem ehrlichen Cliffhanger "eine enge Schranke ist keine Lösung" -
naives Aufrunden traf das Optimum nur in ~55 % der Fälle, bei einer
konkreten Instanz sogar 9 statt 6 Rollen. Dieses Stück löst genau das exakt.

## Warum der Master hier auf einzelnen Stücken statt Auftragstypen basiert

Echte Ryan-Foster-Verzweigung (SAME/DIFFER auf einem Zeilenpaar) ist für
Mengendeckung definiert - eine "Zeile" muss durch genau eine Spalte gedeckt
sein. Das trifft nur zu, wenn jede Zeile eine EINZELNE physische Einheit ist,
nicht ein Auftragstyp mit Bedarf > 1. Deshalb expandiert dieses Stück - wie
`cutting-stock-branch-bound-demo` - auf einzelne Stücke für den Master; die
Spaltengenerierung selbst bleibt pro Knoten ein echtes Spalten-Verfahren.

## Ryan-Foster-Verzweigung

Bei einer fraktionalen Lösung: das fraktionalste Stückpaar aus
UNTERSCHIEDLICHEN Auftragstypen (gleiche Typen sind austauschbar - ein
direkter Rückgriff auf die Symmetrie-Lektion aus
`cutting-stock-cutting-planes-demo`). Zwei Kinder: **ZUSAMMEN** (jedes
künftige Muster enthält beide Stücke oder keines) oder **GETRENNT** (kein
künftiges Muster darf beide enthalten). Wirkt direkt im Pricing-
Teilproblem - ein BESCHRÄNKTER 0/1-Rucksack über einzelne Stücke, gelöst per
rekursivem Branch & Bound (ein Rückgriff auf `branch-bound-demo`, das
allererste Stück der ganzen Konzepte-Reihe).

## Zwei echte Bugs gefunden und behoben, nicht nur angenommen

**Bug 1 - LP-Entartung beim Pricing**: die Spaltengenerierung kann in einer
entarteten Dualwerte-Schleife das immer gleiche, bereits bekannte Muster
wiederfinden und fälschlich "kein verbesserndes Muster mehr" schließen -
konkret nachgewiesen: eine ungültige Schranke von 4.0 statt korrekt 3.0. Fix:
das Pricing sucht explizit nach dem besten NOCH NICHT bekannten Muster.

**Bug 2 - fehlerhafte Abschneide-Bedingung**: eine ursprünglich
verschachtelte Prüfung verhinderte korrektes Abschneiden - Knotenzahlen
explodierten auf über 1000 ohne je eine Lösung zu finden. Fix: eine einzige,
klare Bedingung.

Nach beiden Fixes: 186+ Zufallsinstanzen (n_types 2-7, max_demand 1-4) alle
korrekt gegen Bruteforce geprüft, größte Instanz < 1,4 s. Zusätzlich
verifiziert: Kind-Knoten starten die Spaltengenerierung mit den (gefilterten)
Mustern des Elternknotens statt bei null - ein klar messbarer
Geschwindigkeitsgewinn.

## Der eigentliche Beweis

Auf genau der Instanz aus `column-generation-demo`s Preset "Schranke eng,
Rundung daneben" (n=7, max_demand=4, seed=14) liefert dieses Stück **6** (das
korrekte Optimum), wo naives Aufrunden dort **9** lieferte - der direkte,
jetzt tatsächlich geschlossene Kreis.

## Verifikation

- **Bruteforce-Cross-Check** über einen breiten Sweep.
- **OR-Tools-CP-SAT-Cross-Check** auf allen drei Presets.
- **Cross-Repo-Regressionstest**: reproduziert `column-generation-demo`s
  gescheiterte Instanz und prüft, dass dieses Stück 6 (nicht 9) liefert.
- **Bug-1- und Bug-2-Regressionstests**: verankern beide gefundenen Fixes.
- **Sicherheitsgrenzen-Test**.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, Baum-Animation, Lücken-Vergleich, Formulierungs-Expander |
| `bap_constants.py` | Defaults, Regler-Grenzen, Sicherheitsgrenzen, `PRESETS` |
| `bap_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `bap_scenario.py` | Zufällige Cutting-Stock-Instanzen, Stück-Expansion mit Auftragstyp |
| `bap_pricing.py` | Pricing-Teilproblem (beschränkter 0/1-Rucksack, degenerationsfest) |
| `bap_master.py` | Mengendeckungs-LP über einzelne Stücke inkl. Dual-Werte |
| `bap_solver.py` | Branch-&-Price-Baum mit Ryan-Foster-Verzweigung und Warmstart |
| `bap_bruteforce.py` | Unabhängige Referenzlösung (vollständige Enumeration) |
| `bap_ortools_reference.py` | Echter Google-OR-Tools-CP-SAT-Solver |
| `bap_evaluation.py` | Kennzahlen, Rundung-vs-exakt-Vergleich |
| `bap_visualization.py` | Suchbaum- und Vergleichsdiagramm (Plotly) |
| `tests/` | Bruteforce- und OR-Tools-Cross-Check, Bug-Regressionen, Cross-Repo-Beweis, Sicherheitsgrenzen |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
