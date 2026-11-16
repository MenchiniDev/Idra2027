# Testa 3 (occhio singolo) — piatti da stampare (4)

Ogni cartella `Piatto_<X>` contiene:
- `Testa3_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
  (File → Apri progetto), controllare tipo di piatto e supporti, premere *Slice* e stampare;
- `NN_<pezzo>.stl` — gli stessi pezzi già posizionati, di riserva (importandoli a mano Bambu Studio potrebbe
  ridisporli: meglio il 3MF);
- `piatto.png` — la disposizione vista dall'alto.

Impostazioni salvate nel progetto: A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, **supporti tree(auto)
a 30°** (come la testa 1), piatto **Textured PEI** (cambiarlo in alto se si usa un altro piatto). Prima di
tagliare verificare comunque in Processo → Supporto che *Abilita supporti* sia attivo. Nei pezzi print-in-place
(`CoreY`, `XAxisA/B`, `Palpebre`) controllare nell'anteprima che i supporti non finiscano negli spazi tra le parti
mobili (eventualmente toglierli col pennello).

**Palpebre già montate**: `Palpebre_L_PIP` / `Palpebre_R_PIP` sono tutte le palpebre di un lato in un pezzo solo
(palpebra superiore + tirante + squadretta + `LinkB` + palpebra inferiore), con i giunti print-in-place come quelli
di Will: niente `PinB` e niente viti sul tirante. Dopo la stampa togliere i supporti e muovere a mano ogni giunto
finché gira libero (soprattutto il perno biconico tra squadretta e `LinkB`, che appoggia sul piatto).

**`Piatto_A` e `Piatto_C` contengono anche pezzi della testa 4** (vedi `../README.md`): metterli da parte.

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_1_basi` | 2 | `Base_L` + `Base_R` | ~6 h 24 min | ~230 g | 67 mm |
| `Piatto_A` | 7 | `XAxisA_PIP` + `Palpebre_L_PIP` + `Eyeball` + 4 `BaseKey` | ~10 h 29 min | ~272 g | 122 mm |
| `Piatto_B` | 3 | `XAxisB_PIP` + `CoreY_PIP` + `PivotCentral` | ~7 h 23 min | ~189 g | 112 mm |
| `Piatto_C` | 4 | 2 `PivotOuter_L` + 2 `PivotCentral` | ~2 h 55 min | ~90 g | 24 mm |
| **Totale** | **16** | **4 piatti** | **~27 h 12 min** | **~0.78 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
