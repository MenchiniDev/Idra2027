# Meccanica

Occhi animatronici: **EyeMech ε3.2** di Will Cogley ingrandito, con le palpebre a 1 servo per occhio
(idea da *MorganManly*). Dettagli, liste di stampa e montaggio in `docs/mechanical_eyes.md`.
Licenza dei modelli di partenza **CC BY-NC-SA 4.0** → vedi `docs/mechanical_eyes.md` § Licenza.

## Cartelle
| Cartella | Contenuto |
|---|---|
| `eyes/original/eyemech_e3.2/` | EyeMech ε3.2 di Will Cogley: 3MF, STL, PDF di montaggio, codice, scheda |
| `eyes/original/morganmanly/` | Animatronic Eyes di MorganManly ([Instructables](https://www.instructables.com/Animatronic-Eyes-Double-and-Single-Fully-3D-Printe/), [GitHub](https://github.com/ManlyMorgan/Animatronic-Eye)): `single_v4`, `double_compact` |
| `eyes/eyemech_D85/` | **versione in uso**: occhi a 200 mm tra i centri (bulbo Ø85.3), 4 servo SG90/MG90S in sedi 1:1, base di Will tagliata con linguetta PCA9685 1:1, `info.txt` con quote e viteria; `print_A1/` = pezzi grandi già disposti sui piatti Bambu A1 |
| `eyes/idra_version/` | **idra_version**: stessi pezzi nella scala di Will (bulbo Ø32), palpebre a 1 servo per occhio, da stampare per prima; `bambu_A1/` = un piatto A1 con tutti i pezzi, già tagliato (≈ 4 h 26 min, 98 g) |
| `scripts/generate_eyemech.py` | generatore di entrambe (`--small`, `--interasse`, `--d`, verifica interferenze, `--render`) |
| `scripts/pack_plate.py` | dispone i pezzi di una versione su piatti A1 e li taglia con Bambu Studio (tempo e filamento) |
| `legs/` | pezzi delle gambe (ginocchio, snodi) |
| `enclosures/` | chassis elettronica (da fare) |

## Rigenerare
```bash
pip install trimesh manifold3d numpy scipy shapely pyvista
python mechanical/scripts/generate_eyemech.py            # D85 + print_A1
python mechanical/scripts/generate_eyemech.py --small    # versione di prova
```
