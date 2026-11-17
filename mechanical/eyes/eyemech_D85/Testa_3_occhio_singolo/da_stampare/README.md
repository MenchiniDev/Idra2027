# Testa 3 (occhio singolo) — piatti da stampare (3)

Solo i pezzi della testa 3 (occhio sinistro), nessun pezzo per altre teste. Ogni cartella `Piatto_<X>` contiene:
- `Testa3_Piatto_<X>.3mf` — **progetto Bambu Studio con i pezzi già disposti, non ancora tagliato**: aprirlo
  (File → Apri progetto), controllare tipo di piatto e supporti, premere *Slice* e stampare;
- `NN_<pezzo>.stl` — gli stessi pezzi già posizionati, di riserva (importandoli a mano Bambu Studio potrebbe
  ridisporli: meglio il 3MF);
- `piatto.png` — la disposizione vista dall'alto.

Impostazioni salvate nel progetto: A1 0.4, `0.20mm Standard @BBL A1`, Bambu PLA Basic, **supporti tree(auto)
a 30°**, piatto **Textured PEI** (cambiarlo in alto se si usa un altro piatto). Prima di tagliare verificare
comunque in Processo → Supporto che *Abilita supporti* sia attivo. Nei pezzi print-in-place (`CoreY`,
`XAxisA/B_singolo`, `Palpebre`) controllare nell'anteprima che i supporti non finiscano negli spazi tra le parti
mobili. Le palpebre (`Palpebre_L_PIP`) escono già montate: dopo la stampa togliere i supporti e muovere a mano i
giunti finché girano liberi.

<!-- tabella piatti: generata da mechanical/scripts/teste_D85.py -->

| Piatto | Pezzi | Contenuto | Tempo | Filamento | Altezza max |
|---|---|---|---|---|---|
| `Piatto_A` | 4 | `Base_L` + `Palpebre_L_PIP` + 2 `BaseKey` | ~8 h 32 min | ~249 g | 122 mm |
| `Piatto_B` | 4 | `Base_R_singolo` + `CoreY_PIP` + `XAxisA_singolo` + `XAxisB_singolo` | ~9 h 01 min | ~231 g | 112 mm |
| `Piatto_C` | 4 | `Eyeball` + `PivotOuter_L` + 2 `PivotCentral` | ~3 h 49 min | ~125 g | 53 mm |
| **Totale** | **12** | **3 piatti** | **~21 h 22 min** | **~0.60 kg** | |

Tempi e grammi con `~` sono stime (media per pezzo misurata nei G-code dei piatti della testa 1, supporti compresi, senza riscaldamento e calibrazione iniziale): quelli esatti li dà Bambu Studio dopo *Slice*.
