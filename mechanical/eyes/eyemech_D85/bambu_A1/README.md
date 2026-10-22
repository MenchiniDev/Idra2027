# Piatti Bambu Lab A1 — EyeMech D85

Progetti già tagliati con Bambu Studio 2.05 (A1, ugello 0.4, `0.20mm Standard @BBL A1`,
Bambu PLA Basic), con supporti `tree(auto)` a 30° come nel 3MF di Will, 2 pareti, riempimento 15%.
Si aprono in Bambu Studio (File → Apri progetto).

**Attenzione — supporti**: aprendo il progetto in Bambu Studio e premendo *Slice*, il processo torna il
`0.20mm Standard @BBL A1` di sistema **senza supporti** (le palpebre danno "sbalzo flottante"). Prima di
tagliare: Processo → Supporto → **Abilita supporti** (tipo albero(auto), angolo 30°).

I pezzi sono incastrati sulle loro impronte reali (rotazioni a 15°, ≥ 4 mm tra i pezzi, 3 mm dal bordo):
5 piatti in tutto invece di 9, **una cartella per piatto** (`Piatto_0` … `Piatto_4`) con il progetto
`Piatto_<n>.3mf` già tagliato, gli STL già posizionati sul piatto (per rifare lo slicing a mano) e `piatto.png`
con la disposizione. Disposizione di tutti i piatti in `layout_piatti.json`.

| Piatto | Contenuto | Tempo | Filamento | Altezza |
|---|---|---|---|---|
| 0 | 2 `Eyeball` + `LidBottom_L_PIP` + `LidBottom_R_PIP` + 2 chiavette + 2 `PinB` | 7 h 43 min | 229 g | 121 mm |
| 1 | `Base_L` + `Base_R` incastrate | 6 h 24 min | 230 g | 67 mm |
| 2 | `XAxisA_PIP` + `CoreY_PIP` + `PivotOuter_L` | 7 h 54 min | 190 g | 112 mm |
| 3 | `XAxisB_PIP` + `LidTop_R_PIP` | 5 h 51 min | 127 g | 109 mm |
| 4 | `LidTop_L_PIP` + `PivotOuter_R` + 2 `PivotCentral` | 4 h 32 min | 142 g | 109 mm |
| **Totale** | **5 piatti** | **≈ 32 h 25 min** | **≈ 0.92 kg** | |

Tempi da riga di comando, senza riscaldamento e calibrazione iniziale, che sull'A1 aggiungono qualche minuto
(il piatto 0, in stampa dal 22/10, in Bambu Studio dava 7 h 49 min con la preparazione).
I piatti 2, 3 e 4 contengono le squadrette (`CoreY`, `XAxisB`, `LidTop`): dipendono dalle misure della
squadretta originale del servo (`STOCK_HORN` in `generate_eyemech.py`).

`LidBottom_*_PIP` = palpebra inferiore + `LinkB` stampati insieme (giunto print-in-place sull'orecchia).
Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`) controllare nell'anteprima che i supporti
automatici non finiscano negli spazi tra le parti mobili (eventualmente toglierli col pennello).

Rigenerare (dopo `generate_eyemech.py`; ricrea le cartelle): `python mechanical/scripts/plates_D85.py` (tutti) oppure
`python mechanical/scripts/plates_D85.py 2 3 4` (solo quelli con le squadrette). Lo script rimette gli STL
attuali nelle posizioni di `layout_piatti.json` e stampa la distanza minima tra i pezzi: se un pezzo cambia
ingombro e la distanza scende sotto ~3 mm, la disposizione va rifatta.
