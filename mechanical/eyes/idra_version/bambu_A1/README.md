# Piatto Bambu Lab A1 — idra_version (scala di Will)

**Tutti i pezzi su un solo piatto**: `Piatto_unico/idra_version_Piatto_unico.3mf`, progetto Bambu Studio con i pezzi
già disposti, **da tagliare** (A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, supporti `tree(auto)` 30°,
piatto Textured PEI). Nella cartella anche gli STL già posizionati e `piatto.png`; disposizione in `layout_piatti.json`
(rifare: `python mechanical/scripts/teste_D85.py costruisci mechanical/eyes/idra_version/bambu_A1`).

Pezzi: base di Will tagliata (con linguetta per il PCA9685), 1 fermo servo Y + 2 fermi palpebre, `XAxisA/B`,
`CoreY`, **palpebre di ogni lato in un pezzo solo, già montate** (`Palpebre_L_PIP`, `Palpebre_R_PIP`: superiore +
tirante + squadretta a V + `LinkB` + inferiore, giunti print-in-place come quelli di Will, niente `PinB`), 2 bulbi,
2 supporti centrali e 2 esterni.

Versioni precedenti: con `PinB` a parte e vite M2×8 (19 pezzi, 4 h 26 min, 98 g); base ridotta con sedi nuove
(senza fermi), 16 pezzi, 4 h 01 min, 78 g; `LinkB` separati + rondelle, 20 pezzi, 3 h 52 min, 76 g; base intera di
Will + 3 fermi servo: 4 h 58 min, 117 g.

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_unico` | 15 | `Base` + `XAxisB_PIP` + `Palpebre_L_PIP` + `Palpebre_R_PIP` + `XAxisA_PIP` + `CoreY_PIP` + `PivotOuter_R` + `PivotOuter_L` + 2 `PivotCentral` + 2 `Eyeball` + `Retainer_Single` + 2 `Retainer_Lid` | — | — | 46 mm |
| **Totale** | **15** | **1 piatto** | **—** | **—** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
