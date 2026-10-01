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
| `scripts/generate_eyes.py` | generatore parametrico (rigenera tutto, accetta diametri custom) |
| `enclosures/` | chassis elettronica (da fare) |

## Rigenerare
```bash
pip install trimesh manifold3d numpy scipy fast_simplification
python mechanical/scripts/generate_eyes.py          # 50, 70, 90
python mechanical/scripts/generate_eyes.py 60 80    # diametri a scelta
```
