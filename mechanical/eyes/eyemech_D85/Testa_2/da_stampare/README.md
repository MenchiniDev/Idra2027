# Testa 2 — piatti da stampare (3)

Ogni cartella `Piatto_<X>` contiene:
- `Testa2_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
  (File → Apri progetto), controllare tipo di piatto e supporti, premere *Slice* e stampare;
- `NN_<pezzo>.stl` — gli stessi pezzi già posizionati, di riserva (importandoli a mano Bambu Studio potrebbe
  ridisporli: meglio il 3MF);
- `piatto.png` — la disposizione vista dall'alto.

Impostazioni salvate nel progetto: A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, **supporti tree(auto)
a 30°** (come la testa 1), piatto **Textured PEI** (cambiarlo in alto se si usa un altro piatto). Prima di
tagliare verificare comunque in Processo → Supporto che *Abilita supporti* sia attivo: senza supporti le
palpebre danno "sbalzo flottante". Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`)
controllare nell'anteprima che i supporti non finiscano negli spazi tra le parti mobili.

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_A` | 8 | `XAxisA_PIP` + `LidTop_R_PIP` + `LidTop_L_PIP` + `PivotOuter_L` + 2 `BaseKey` + 2 `PinB` | ~9 h 49 min | ~236 g | 109 mm |
| `Piatto_B` | 3 | `XAxisB_PIP` + `CoreY_PIP` + `LidBottom_R_PIP` | ~8 h 42 min | ~218 g | 121 mm |
| `Piatto_C` | 4 | `PivotOuter_R` + 2 `PivotCentral` + `LidBottom_L_PIP` | ~4 h 11 min | ~124 g | 121 mm |
| **Totale** | **15** | **3 piatti** | **~22 h 43 min** | **~0.58 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
