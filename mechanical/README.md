# Meccanica

Occhi animatronici: **EyeMech ε3.2** di Will Cogley ingrandito, con le palpebre a 1 servo per occhio
(idea da *MorganManly*). Dettagli, liste di stampa e montaggio in `docs/mechanical_eyes.md`.
Licenza dei modelli di partenza **CC BY-NC-SA 4.0** → vedi `docs/mechanical_eyes.md` § Licenza.

## Cartelle
| Cartella | Contenuto |
|---|---|
| `eyes/original/eyemech_e3.2/` | EyeMech ε3.2 di Will Cogley: 3MF, STL, PDF di montaggio, codice, scheda |
| `eyes/original/morganmanly/` | Animatronic Eyes di MorganManly ([Instructables](https://www.instructables.com/Animatronic-Eyes-Double-and-Single-Fully-3D-Printe/), [GitHub](https://github.com/ManlyMorgan/Animatronic-Eye)): `single_v4`, `double_compact` |
| `eyes/eyemech_D85/` | **versione in uso**: occhi a 200 mm tra i centri (bulbo Ø85.3), 4 servo SG90/MG90S in sedi 1:1, base di Will tagliata con linguetta PCA9685 1:1, `info.txt` con quote e viteria; `pezzi/` = un STL per pezzo; **`Testa_1` … `Testa_4` = i piatti Bambu A1 di ogni testa** (stato e cosa stampare in `eyemech_D85/README.md`) |
| `eyes/idra_version/` | **idra_version**: stessi pezzi nella scala di Will (bulbo Ø32), palpebre a 1 servo per occhio, da stampare per prima; `bambu_A1/` = un piatto A1 con tutti i pezzi, già tagliato (≈ 4 h 26 min, 98 g) |
| `scripts/generate_eyemech.py` | generatore di entrambe (`--small`, `--interasse`, `--d`, verifica interferenze, `--render`) |
| `scripts/teste_D85.py` | piatti A1 delle teste D85: incastra i pezzi sulle impronte reali e scrive per ogni piatto progetto Bambu Studio (3MF), STL posizionati e immagine (`--taglia` sul PC: anche lo slicing) |
| `scripts/pack_plate.py` | dispone i pezzi della idra_version su un piatto A1 e lo taglia con Bambu Studio (tempo e filamento) |
| `mandibola/` | **supporto regolabile del servo della mandibola** (DS3225 25 kg) appeso alla base degli occhi D85: pezzi, piatto A1 con 2 set, viti e montaggio nel suo `README.md` |
| `scripts/mandibola_DS3225.py` | genera i pezzi del supporto mandibola e il loro piatto A1 |
| `legs/` | pezzi delle gambe (ginocchio, snodi) |
| `enclosures/` | chassis elettronica (da fare) |

## Rigenerare
```bash
pip install trimesh manifold3d numpy scipy shapely pyvista
python mechanical/scripts/generate_eyemech.py            # D85 (STL in eyemech_D85/pezzi)
python mechanical/scripts/generate_eyemech.py --small    # versione di prova
python mechanical/scripts/teste_D85.py costruisci mechanical/eyes/eyemech_D85/Testa_2/da_stampare   # rifà i piatti di una cartella
```
