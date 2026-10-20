# Piatto Bambu Lab A1 — idra_version (scala di Will)

**Tutti i 20 pezzi su un solo piatto** (`idra_version_Piatto_unico.3mf`), già tagliato con Bambu Studio 2.05:
A1, ugello 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, supporti `tree(auto)` 30°, 2 pareti,
riempimento 15%. Si apre con File → Apri progetto.

| | |
|---|---|
| Tempo | **≈ 3 h 52 min** (senza riscaldamento/calibrazione iniziale) |
| Filamento | **≈ 76 g** PLA |
| Altezza massima | 42 mm |
| Pezzi | base ridotta, `XAxisA/B`, `CoreY`, 2 palpebre superiori e 2 inferiori, 2 `LinkB`, 2 bulbi, 2 supporti centrali e 2 esterni, 2 `PinB`, 2 rondelle |

Disposizione in `docs/img/idra_version_piatto.png` (6 mm tra i pezzi, margine 3 mm dal bordo).
Se i supporti si toccano o vuoi più spazio: `python mechanical/scripts/pack_plate.py idra_version --gap 8`
(se non ci stanno più tutti: `--plates 2`).
Se un pezzo si stacca durante la stampa si rischia di rovinare anche gli altri: in quel caso dividere
con `--plates 2`.

Versione precedente (base intera di Will + 3 fermi servo): 4 h 58 min, 117 g.
