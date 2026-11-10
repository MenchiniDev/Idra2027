# Testa 4 (occhio singolo) — piatti da stampare (3)

Ogni cartella `Piatto_<X>` contiene:
- `Testa4_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
  (File → Apri progetto), controllare tipo di piatto e supporti, premere *Slice* e stampare;
- `NN_<pezzo>.stl` — gli stessi pezzi già posizionati, di riserva (importandoli a mano Bambu Studio potrebbe
  ridisporli: meglio il 3MF);
- `piatto.png` — la disposizione vista dall'alto.

Impostazioni salvate nel progetto: A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, **supporti tree(auto)
a 30°** (come la testa 1), piatto **Textured PEI** (cambiarlo in alto se si usa un altro piatto). Prima di
tagliare verificare comunque in Processo → Supporto che *Abilita supporti* sia attivo: senza supporti le
palpebre danno "sbalzo flottante". Nei pezzi print-in-place (`CoreY`, `XAxisA/B`, `LidTop`, `LidBottom`)
controllare nell'anteprima che i supporti non finiscano negli spazi tra le parti mobili.

I pezzi della testa 4 che mancano qui escono dai piatti `A` e `C` della testa 3 (vedi `../README.md`).

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_1_basi` | 2 | `Base_L` + `Base_R` | ~6 h 24 min | ~230 g | 67 mm |
| `Piatto_D` | 3 | `XAxisA_PIP` + `CoreY_PIP` + `PivotOuter_L` | ~7 h 49 min | ~192 g | 112 mm |
| `Piatto_E` | 3 | `XAxisB_PIP` + `LidTop_L_PIP` + `PivotCentral` | ~6 h 19 min | ~159 g | 109 mm |
| **Totale** | **8** | **3 piatti** | **~20 h 32 min** | **~0.58 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
