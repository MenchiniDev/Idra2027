# Meccanica — Occhi animatronici

Base di partenza: **"Animatronic Eyes – Double and Single"** di *MorganManly*
([Instructables](https://www.instructables.com/Animatronic-Eyes-Double-and-Single-Fully-3D-Printe/),
[GitHub](https://github.com/ManlyMorgan/Animatronic-Eye)).
Licenza originale **CC BY-NC-SA 4.0** → vedi `docs/mechanical_eyes.md` § Licenza.

## Cartelle
| Cartella | Contenuto |
|---|---|
| `eyes/original/single_v4` | STL originali occhio singolo (Ø35 mm) |
| `eyes/original/double_compact` | STL originali doppio occhio |
| `eyes/scaled/D50`, `D70`, `D90` | occhi ingranditi Ø50 / Ø70 / Ø90 mm + `info.txt` con quote e viteria |
| `eyes/scaled/double/D50`…`D90` | coppia di occhi, 6 servo (3 per occhio, indipendenti) |
| `eyes/scaled/double_2servo/D50`…`D90` | **coppia a 2 servo** (sx/dx e palpebre sincronizzati): solo i pezzi aggiuntivi, il resto da `double/` — vedi `docs/mechanical_eyes.md` |
| `eyes/scaled/double_2servo_mg995/D50`…`D90` | **coppia a 2 servo MG995**: piastra nuova senza vani MG90S + squadretta doppia + barra palpebre |
| `eyes/original/eyemech_e3.2/src` | EyeMech ε3.2 di Will Cogley (3MF, PDF di montaggio, codice) — CC BY-NC-SA 4.0 |
| `eyes/scaled/hybrid_eyemech/D85` | **ibrido EyeMech (assi X/Y) + MorganManly (palpebre), 4 SG90**, bulbo Ø85 — vedi `docs/mechanical_eyes.md` |
| `scripts/generate_eyes.py` | generatore parametrico (rigenera tutto, accetta diametri custom) |
| `scripts/generate_hybrid.py` | generatore dell'ibrido (`--cm`, `--plus`, `--horn-h`, verifica interferenze, `--render`) |
| `enclosures/` | chassis elettronica (da fare) |

## Rigenerare
```bash
pip install trimesh manifold3d numpy scipy fast_simplification
python mechanical/scripts/generate_eyes.py          # 50, 70, 90
python mechanical/scripts/generate_eyes.py 60 80    # diametri a scelta
python mechanical/scripts/generate_eyes.py --sync   # solo i pezzi della coppia a 2 servo
python mechanical/scripts/generate_eyes.py --mg995  # solo la coppia a 2 servo MG995
pip install shapely                                 # in piu' per l'ibrido
python mechanical/scripts/generate_hybrid.py        # ibrido, bulbo 85 mm
python mechanical/scripts/generate_hybrid.py --plus 1.5   # 8.5 cm + 1.5 cm = 10 cm
```
