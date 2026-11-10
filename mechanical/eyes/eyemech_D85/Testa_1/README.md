# Testa 1 — coppia di occhi — ✅ COMPLETA

I 5 piatti con cui è stata stampata la testa 1 (prima stavano in `bambu_A1/`). Restano come riferimento o
per ristampare un pezzo rotto: **da qui non c'è più niente da stampare**.

Progetti già tagliati con Bambu Studio 2.05 (A1, ugello 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic),
supporti `tree(auto)` a 30° come nel 3MF di Will, 2 pareti, riempimento 15%. Ogni cartella `Piatto_<n>` ha il
progetto `Piatto_<n>.3mf`, gli STL già posizionati sul piatto (per rifare lo slicing a mano) e `piatto.png`.
Disposizione di tutti i piatti in `layout_piatti.json`.

**Attenzione — supporti**: aprendo questi progetti in Bambu Studio e premendo *Slice*, il processo torna il
`0.20mm Standard @BBL A1` di sistema **senza supporti** (le palpebre danno "sbalzo flottante"). Prima di
tagliare: Processo → Supporto → **Abilita supporti** (tipo albero(auto), angolo 30°).

| Piatto | Contenuto | Tempo | Filamento | Altezza |
|---|---|---|---|---|
| 0 | 2 `Eyeball` + `LidBottom_L_PIP` + `LidBottom_R_PIP` + 2 chiavette + 2 `PinB` | 7 h 43 min | 229 g | 121 mm |
| 1 | `Base_L` + `Base_R` incastrate | 6 h 24 min | 230 g | 67 mm |
| 2 | `XAxisA_PIP` + `CoreY_PIP` + `PivotOuter_L` | 7 h 54 min | 190 g | 112 mm |
| 3 | `XAxisB_PIP` + `LidTop_R_PIP` | 5 h 51 min | 127 g | 109 mm |
| 4 | `LidTop_L_PIP` + `PivotOuter_R` + 2 `PivotCentral` | 4 h 32 min | 142 g | 109 mm |
| **Totale** | **5 piatti** | **≈ 32 h 25 min** | **≈ 0.92 kg** | |

Tempi da riga di comando, senza riscaldamento e calibrazione iniziale, che sull'A1 aggiungono qualche minuto.
I piatti 2, 3 e 4 contengono le squadrette (`CoreY`, `XAxisB`, `LidTop`): dipendono dalle misure della
squadretta originale del servo (`STOCK_HORN` in `generate_eyemech.py`).

`LidBottom_*_PIP` = palpebra inferiore + `LinkB` stampati insieme (giunto print-in-place sull'orecchia).
Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`) controllare nell'anteprima che i supporti
automatici non finiscano negli spazi tra le parti mobili (eventualmente toglierli col pennello).

Rifare questi piatti con gli STL attuali di `../pezzi/` (escono non tagliati; con `--taglia`, sul PC con
Bambu Studio, escono tagliati): `python mechanical/scripts/teste_D85.py costruisci mechanical/eyes/eyemech_D85/Testa_1`.
