# EyeMech D85 — piatti di stampa delle teste dell'Idra

Stampante: **Bambu Lab A1** (piatto 256 × 256), PLA, 0.20 mm. In ogni piatto ci sono più pezzi possibile
(incastrati sulle impronte reali, ≥ 4 mm tra i pezzi, 3 mm dal bordo) per fare meno stampe possibile.

## Stato

| Testa | Occhi | Stato | Cosa resta da stampare | Cartella |
|---|---|---|---|---|
| 1 | coppia | ✅ completa | niente | [`Testa_1/`](Testa_1/) |
| 2 | coppia | 🟡 basi stampate, bulbi già pronti | **3 piatti**, ~22 h 45 min, ~0.58 kg | [`Testa_2/da_stampare/`](Testa_2/da_stampare/) |
| 3 | singolo (sx) | ⏳ da stampare | **4 piatti**, ~30 h, ~0.87 kg (con 5 pezzi della testa 4) | [`Testa_3_occhio_singolo/da_stampare/`](Testa_3_occhio_singolo/da_stampare/) |
| 4 | singolo (sx) | ⏳ da stampare | **3 piatti**, ~20 h 30 min, ~0.58 kg | [`Testa_4_occhio_singolo/da_stampare/`](Testa_4_occhio_singolo/da_stampare/) |
| | | | **Totale: 10 piatti, ~73 h, ~2.0 kg** | |

Tempi e grammi con `~` sono stime (per ogni pezzo la media misurata nei G-code dei piatti della testa 1, supporti
compresi): quelli esatti li dà Bambu Studio dopo *Slice*.

## Cartelle

| Cartella | Contenuto |
|---|---|
| `pezzi/` | un STL per pezzo, nell'orientamento di stampa (li genera `mechanical/scripts/generate_eyemech.py`) |
| `info.txt` | quote, servo, viteria, ingombri dei pezzi |
| `Testa_1/` | i 5 piatti (già tagliati) con cui è stata stampata la testa 1 |
| `Testa_2/gia_stampati/` | il piatto delle basi della testa 2, già stampato (lo stesso piatto 1 della testa 1) |
| `Testa_2/da_stampare/` | i 3 piatti con tutto il resto della testa 2, **senza i bulbi** (già pronti) |
| `Testa_3_occhio_singolo/da_stampare/` | 4 piatti: testa 3 completa + 5 pezzi per la testa 4 |
| `Testa_4_occhio_singolo/da_stampare/` | 3 piatti: il resto della testa 4 |

Ogni cartella `Piatto_<X>` ha il progetto Bambu Studio (`.3mf`), gli STL già posizionati e `piatto.png` con la
disposizione; ogni cartella di piatti ha `layout_piatti.json` (pezzo, rotazione e posizione su ogni piatto) e un
`README.md` con contenuto, tempi e grammi di ogni piatto. I progetti nuovi (teste 2, 3, 4) **non sono tagliati**:
si aprono in Bambu Studio, si controlla piatto e supporti (già attivi, tree(auto) 30°) e si preme *Slice*.

## Testa a occhio singolo (teste 3 e 4)

Stesso meccanismo D85 e **stessi STL** della coppia, montato con **un solo occhio, il sinistro**: nessun pezzo
nuovo da verificare.

- **Si stampa**: tutta la parte centrale — base intera (`Base_L` + `Base_R` + 2 chiavette: la sede del servo Y è
  a cavallo della giunzione), i 2 `PivotCentral` (reggono i perni del `CoreY`), `CoreY`, `XAxisA`, `XAxisB` — più
  i pezzi del solo lato sinistro: 1 `Eyeball`, `PivotOuter_L`, `LidTop_L`, `LidBottom_L`, 1 `PinB`.
- **Non si stampa**: `PivotOuter_R`, `LidTop_R`, `LidBottom_R`, il secondo bulbo e il secondo `PinB`.
- **3 servo**: X, Y e palpebre sinistre. La sede delle palpebre destre in `Base_R` resta vuota.
- `XAxisB` (squadretta del servo X + tirante + adattatori) fa il parallelogramma con il solo occhio sinistro;
  gli adattatori dell'estremità destra di `XAxisA` e `XAxisB` restano liberi, senza bulbo.
- Ingombro uguale alla coppia (base 388 mm): l'occhio sta a 100 mm a sinistra del centro del meccanismo.
- Occhio a destra invece che a sinistra: stessi piatti, sostituendo `PivotOuter_L`, `LidTop_L`, `LidBottom_L`
  con i `_R` (si rifà la disposizione con lo script, vedi sotto).

Le teste 3 e 4 sono uguali, quindi i loro pezzi sono incastrati insieme: **7 piatti per tutte e due invece di 8**,
e la testa 3 è completa già dopo i suoi 4 piatti (i pezzi della testa 4 che escono dai piatti `A` e `C` della
testa 3 sono elencati in `Testa_3_occhio_singolo/README.md`).

## Rifare i piatti

Dopo aver rigenerato i pezzi (`generate_eyemech.py`), rimettere gli STL nuovi nelle stesse posizioni:
```bash
pip install trimesh shapely scipy matplotlib
python mechanical/scripts/teste_D85.py costruisci mechanical/eyes/eyemech_D85/Testa_2/da_stampare            # STL, 3MF, png, tabella
python mechanical/scripts/teste_D85.py costruisci mechanical/eyes/eyemech_D85/Testa_2/da_stampare --taglia   # sul PC: anche lo slicing
```
Se un pezzo cambia ingombro e la distanza minima stampata scende sotto ~3 mm, la disposizione va rifatta:
```bash
python mechanical/scripts/teste_D85.py impacchetta coppia_senza_basi_occhi 3        # testa 2
python mechanical/scripts/teste_D85.py impacchetta singolo_senza_basi 5 --copie 2    # teste 3 + 4 (basi a parte)
```
e il JSON stampato va in `layout_piatti.json` (un piatto per elenco, con un nome).
