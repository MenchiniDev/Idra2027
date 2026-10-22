# Piatto Bambu Lab A1 — idra_version (scala di Will)

**Tutti i 19 pezzi su un solo piatto** (`idra_version_Piatto_unico.3mf`), già tagliato con Bambu Studio 2.05:
A1, ugello 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, supporti `tree(auto)` 30°, 2 pareti,
riempimento 15%. Si apre con File → Apri progetto.

| | |
|---|---|
| Tempo | **≈ 4 h 26 min** (senza riscaldamento/calibrazione iniziale) |
| Filamento | **≈ 98 g** PLA |
| Altezza massima | 42 mm |
| Pezzi | base di Will tagliata (con linguetta per il PCA9685), 1 fermo servo Y + 2 fermi palpebre, `XAxisA/B`, `CoreY`, 2 palpebre superiori (con tirante e squadretta a V) e 2 inferiori (con `LinkB`, print-in-place), 2 bulbi, 2 supporti centrali e 2 esterni, 2 `PinB` |

Disposizione in `docs/img/idra_version_piatto.png` (6 mm tra i pezzi, margine 3 mm dal bordo).
Se i supporti si toccano o vuoi più spazio: `python mechanical/scripts/pack_plate.py idra_version --gap 8`
(se non ci stanno più tutti: `--plates 2`).
Se un pezzo si stacca durante la stampa si rischia di rovinare anche gli altri: in quel caso dividere
con `--plates 2`.

Versioni precedenti: base ridotta con sedi nuove (senza fermi), 16 pezzi, 4 h 01 min, 78 g; `LinkB` separati +
rondelle, 20 pezzi, 3 h 52 min, 76 g; base intera di Will + 3 fermi servo:
4 h 58 min, 117 g.
