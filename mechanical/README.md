# Meccanica

Occhi animatronici: **EyeMech ε3.2** di Will Cogley ingrandito, con le palpebre a 1 servo per occhio
(idea da *MorganManly*, [Instructables](https://www.instructables.com/Animatronic-Eyes-Double-and-Single-Fully-3D-Printe/),
[GitHub](https://github.com/ManlyMorgan/Animatronic-Eye)). Licenza dei modelli di partenza e dei
derivati: **CC BY-NC-SA 4.0**.

## Cartelle
| Cartella | Contenuto |
|---|---|
| `eyes/eyemech_D85/` | **versione in uso**: occhi a 200 mm tra i centri (bulbo Ø85.3), 4 servo SG90/MG90S in sedi 1:1, base tagliata con linguetta PCA9685 1:1, `info.txt` con quote e viteria; `pezzi/` = un STL per pezzo; **`Testa_1` … `Testa_4` = i piatti Bambu A1 di ogni testa** (stato e cosa stampare in `eyemech_D85/README.md`) |
| `mandibola/` | **supporto del servo della mandibola** (DS3225 25 kg): guida imbullonata sotto l'estremità sinistra della base degli occhi con 4 bulloni M4 (servo vicino alla cerniera, albero verso l'esterno) + slitta col servo regolabile in altezza, corsa 80 mm (2 viti); pezzi, piatti A1 (1 set, 4 set), fori, viti e montaggio nel suo `README.md` |

Gli script che generano pezzi e piatti (`mechanical/scripts/…`, citati nei README delle teste)
sono sul ramo `archivio`.
