# Testa 4 (occhio singolo) — piatti da stampare (3)

Ogni cartella `Piatto_<X>` contiene:
- `Testa4_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
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

I pezzi della testa 4 che mancano qui escono dai piatti `A` e `C` della testa 3 (vedi `../README.md`).

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_1_basi` | 2 | `Base_L` + `Base_R` | ~6 h 24 min | ~230 g | 67 mm |
| `Piatto_D` | 3 | `XAxisA_PIP` + `Palpebre_L_PIP` + `Eyeball` | ~9 h 58 min | ~259 g | 122 mm |
| `Piatto_E` | 3 | `XAxisB_PIP` + `CoreY_PIP` + `PivotCentral` | ~7 h 23 min | ~189 g | 112 mm |
| **Totale** | **8** | **3 piatti** | **~23 h 46 min** | **~0.68 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
