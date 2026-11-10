# Testa 3 (occhio singolo) — piatti da stampare (4)

Ogni cartella `Piatto_<X>` contiene:
- `Testa3_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
  (File → Apri progetto), controllare tipo di piatto e supporti, premere *Slice* e stampare;
- `NN_<pezzo>.stl` — gli stessi pezzi già posizionati, di riserva (importandoli a mano Bambu Studio potrebbe
  ridisporli: meglio il 3MF);
- `piatto.png` — la disposizione vista dall'alto.

Impostazioni salvate nel progetto: A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, **supporti tree(auto)
a 30°** (come la testa 1), piatto **Textured PEI** (cambiarlo in alto se si usa un altro piatto). Prima di
tagliare verificare comunque in Processo → Supporto che *Abilita supporti* sia attivo: senza supporti le
palpebre danno "sbalzo flottante". Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`)
controllare nell'anteprima che i supporti non finiscano negli spazi tra le parti mobili.

**`Piatto_A` e `Piatto_C` contengono anche pezzi della testa 4** (vedi `../README.md`): metterli da parte.

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_1_basi` | 2 | `Base_L` + `Base_R` | ~6 h 24 min | ~230 g | 67 mm |
| `Piatto_A` | 10 | `XAxisA_PIP` + `CoreY_PIP` + 2 `Eyeball` + 4 `BaseKey` + 2 `PinB` | ~11 h 01 min | ~299 g | 112 mm |
| `Piatto_B` | 3 | `XAxisB_PIP` + `LidTop_L_PIP` + `PivotCentral` | ~6 h 19 min | ~159 g | 109 mm |
| `Piatto_C` | 5 | `PivotOuter_L` + 2 `PivotCentral` + 2 `LidBottom_L_PIP` | ~6 h 13 min | ~178 g | 121 mm |
| **Totale** | **20** | **4 piatti** | **~29 h 57 min** | **~0.87 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
