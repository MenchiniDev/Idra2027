# Piatti Bambu Lab A1 — EyeMech D85

Progetti già tagliati con Bambu Studio 2.05 (A1, ugello 0.4, `0.20mm Standard @BBL A1`,
Bambu PLA Basic), con supporti `tree(auto)` a 30° come nel 3MF di Will, 2 pareti, riempimento 15%.
Si aprono direttamente in Bambu Studio (File → Apri progetto) e si mandano in stampa.

| Piatto | Contenuto | Tempo | Filamento | Altezza |
|---|---|---|---|---|
| 1 | `Base_L` + `Base_R` (base ridotta) + 2 chiavette + 2 `PinB` | 5 h 34 min | 190 g | 67 mm |
| 2 | `XAxisA_PIP` (in diagonale) | 3 h 26 min | 83 g | 37 mm |
| 3 | `XAxisB_PIP` (in diagonale) | 3 h 07 min | 66 g | 30 mm |
| 4 | `CoreY_PIP` + `LidBottom_L_PIP` | 5 h 55 min | 135 g | 121 mm |
| 5 | `LidTop_L_PIP` + `LidTop_R_PIP` | 4 h 48 min | 119 g | 109 mm |
| 6 | `PivotOuter_L` + `PivotOuter_R` | 1 h 13 min | 49 g | 24 mm |
| 7 | `PivotCentral` × 2 | 1 h 20 min | 57 g | 15 mm |
| 8 | `Eyeball` × 2 + `LidBottom_R_PIP` | 5 h 24 min | 168 g | 121 mm |
| **Totale** | **8 piatti** | **≈ 30 h 53 min** | **≈ 0.87 kg** | |

`LidBottom_*_PIP` = palpebra inferiore + `LinkB` stampati insieme (giunto print-in-place sull'orecchia).
Con la disposizione automatica di Bambu Studio le due insieme non stanno né col `CoreY` né coi bulbi:
una va sul piatto 4, l'altra sull'8.

Stime di Bambu Studio (tempi senza riscaldamento/calibrazione iniziale, che sull'A1 aggiungono
qualche minuto per piatto). Con un altro filamento o profilo i valori cambiano: rifare lo slicing.
Ordine consigliato: prima i piatti 2, 3, 4 (assi X/Y e box del servo X) per provare le sedi dei servo,
poi la base.

Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`) controllare nell'anteprima che i supporti
automatici non finiscano negli spazi tra le parti mobili (eventualmente toglierli col pennello).

Rigenerare (dopo `generate_eyemech.py`): aprire i file STL in `../` e `../print_A1/` in Bambu Studio,
oppure usare la riga di comando (`bambu-studio.exe --slice 0 --arrange 1 ... --export-3mf`): piatti 1–3 dai
pezzi già disposti in `../print_A1/P1..P3` (`--arrange 0`), gli altri dai file in `../` (`--arrange 1`),
profili come in `mechanical/scripts/pack_plate.py` (`profiles()`).
