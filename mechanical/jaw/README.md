# Mandibola: supporto servo DS3225

Servo: **DSservo DS3225 (Red)**, 25 kg (corpo 40 x 20 x 40.4, orecchie 54.5, fori 49.5 x 10).
Generatore: `mechanical/scripts/generate_jaw_mount.py` (`--hmin` / `--hmax` per cambiare la corsa).

| Pezzo | Cosa fa |
|---|---|
| `JawMount_Culla.stl` | piastra con la finestra del servo (orecchie avvitate sulla piastra, albero orizzontale) + braccio con asola |
| `JawMount_Testa.stl` | piatto 64 x 44 da incollare a caldo sotto la base degli occhi (fori = rivetti di colla) + codolo con 2 fori M4 |

Altezza dalla bocca del servo (bordo superiore) alla faccia superiore del piatto: **72-98 mm** (85 a meta' corsa).
Montaggio: servo nella culla con 4 autofilettanti M3 (fori pilota 2.6); codolo davanti al braccio,
2 x M4x25 + dadi e rondelle nell'asola; si trova l'altezza sulla testa, si serra, poi si incolla il piatto.

Viti: 4 x M3x12 autofilettanti (servo), 2 x M4x25 + 2 dadi M4 + 4 rondelle.

## Piatto di ristampa (11/2026)
`bambu_A1/Piatto_ristampa/Piatto_ristampa.3mf`: `XAxisA_PIP` della D85 (rotto), 2 `Eyeball` D85 e i due pezzi
del supporto. 8 h 05 min, 238 g, A1 0.4 / 0.20mm Standard / PLA Basic, supporti tree(auto) 30 gradi.
Rigenerare: `python mechanical/scripts/plate_ristampa_jaw.py`.
