# Testa 2 — piatti (3, già stampati)

Ogni cartella `Piatto_<X>` contiene:
- `Testa2_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
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

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_A` | 5 | `XAxisA_PIP` + `Palpebre_L_PIP` + `PivotOuter_L` + 2 `BaseKey` | ~9 h 20 min | ~230 g | 122 mm |
| `Piatto_B` | 2 | `Palpebre_R_PIP` + `XAxisB_PIP` | ~7 h 56 min | ~196 g | 122 mm |
| `Piatto_C` | 4 | `CoreY_PIP` + `PivotOuter_R` + 2 `PivotCentral` | ~5 h 55 min | ~163 g | 112 mm |
| **Totale** | **11** | **3 piatti** | **~23 h 11 min** | **~0.59 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
