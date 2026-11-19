# Supporto del servo della mandibola (DS3225, 25 kg)

Due pezzi stampati che portano il servo grande della mandibola **sotto l'estremità sinistra della base degli
occhi** (`Base_L`), con l'albero rivolto verso l'esterno: così il servo sta vicino alla cerniera della
mandibola e la squadretta la muove con un braccio corto. L'**altezza è regolabile (corsa 80 mm)**: si trova il
punto in cui l'albero combacia con la cerniera, si stringono 2 viti e il servo muove la mandibola (firmware:
`firmware/EyeD85_mandibola`, canale 0 della PCA9685).

![Supporto mandibola](../../docs/img/mandibola_supporto.png)

| Pezzo | Cosa fa |
|---|---|
| `Guida` | **flangia** che si imbullona sotto il blocco pieno in fondo alla base con **4 bulloni M4** + **canale verticale** a U (alto 168 mm), aperto verso l'esterno e in basso, con una fessura verticale su tutti e due i fianchi |
| `Slitta_DS3225` | **incasso preciso del servo**: il corpo entra nella tasca, le orecchie appoggiano sulla faccia e si fissano con le 4 viti del servo. Scorre nel canale (0.3 mm di gioco per lato) e si blocca con **2 viti M4** che passano nella fessura della guida e si avvitano nei dadi infilati nel fianco della slitta |

L'albero del servo resta orizzontale, parallelo all'asse degli occhi, e sporge verso l'esterno: la squadretta
sta circa 35 mm oltre il bordo sinistro della base.

**Regolazione in altezza: 80 mm.** Albero da **40 a 120 mm sotto il fondo della base** col servo montato
nella slitta con l'albero in alto, da 60 a 140 mm con l'albero in basso. Nella posizione più alta restano 8 mm
sopra la slitta per far uscire il cavo del servo.

## Fori nella base (4 × Ø4.5)
All'estremità **sinistra** della base (`Base_L`, quella che c'è in tutte le teste, anche in quelle a occhio
singolo), nel **blocco pieno alto 20.8 mm** oltre il piede del supporto esterno (vedi il disegno, riquadro 1):
- 2 colonne di fori a **7 mm** e **18 mm** dal bordo sinistro della base;
- fila davanti a **18.4 mm** dal bordo davanti della base, fila dietro **72 mm** più indietro.

In quei 4 punti la base è piena per tutti i 20.8 mm. Per segnare i fori basta appoggiare la **flangia sotto la
base** usandola come dima: parete di fondo della guida a **1.5 mm dal piede del supporto esterno**, flangia che
sporge 14.3 mm oltre il bordo sinistro e bordo davanti della flangia 12.4 mm dietro il bordo davanti della base.
Si fora con la punta da 4.5. La flangia occupa quasi tutto il blocco, quindi la posizione avanti/indietro è
praticamente questa.

La guida è simmetrica davanti/dietro: girata di 180° va anche all'estremità destra, se la base lì è intera
(`Base_R`). Le teste a occhio singolo hanno la metà destra corta e lì il blocco non c'è.

## Viti (per testa)
| Dove | Viti | Dadi | Rondelle |
|---|---|---|---|
| Guida → base | 4 × **M4×35** dall'alto | 4 × M4 sotto la flangia | 8 × M4 (sopra la base e sotto la flangia) |
| Slitta → guida (blocco altezza) | 2 × **M4×16** | 2 × M4 nelle sedi sul fianco della slitta | 2 × M4 |
| Servo → slitta | le 4 viti del servo (o 4 autofilettanti ~3×12) | — | — |

## Montaggio
1. Forare la base dall'alto e imbullonare la **guida** sotto l'estremità sinistra: bulloni dall'alto, rondella
   sopra la base e sotto la flangia, dado sotto.
2. Infilare i **2 dadi M4** nelle sedi esagonali sul fianco della slitta.
3. Mettere il **servo nella slitta**: corpo nella tasca (il cavo esce dal passaggio in fondo alla tasca),
   orecchie sulla faccia, 4 viti del servo. Albero in alto o in basso, come serve.
4. Infilare la **slitta nel canale dal basso**, col servo verso il lato aperto (verso l'esterno) e i dadi verso
   uno dei due fianchi (di serie quello davanti).
5. Le **2 viti M4×16** con rondella attraverso la fessura nei dadi della slitta, poco strette: far scorrere la
   slitta finché l'albero è sull'asse della cerniera della mandibola, poi stringere.
6. Squadretta del servo sulla mandibola. Taratura della corsa (chiusa / aperta) col firmware: comando `m<gradi>`
   (es. `m35`) e `CAL_JAW` in `firmware/EyeD85_mandibola/config.h`.

## Stampa
In `stampa/`, un file per piatto (progetti Bambu Studio già disposti, da tagliare; anteprime in `stampa/anteprime/`):
- `Mandibola_supporto_1_set.3mf` — guida + slitta per **una testa**;
- `Mandibola_supporto_4_set.3mf` — **4 set** (tutte le teste) in un solo piatto.

Impostazioni salvate nel progetto: PLA 0.20 mm, **4 pareti, riempimento 25% gyroid, senza supporti** (non
servono), piatto Textured PEI. La guida si stampa in piedi sulla flangia (alta 168 mm), la slitta sul dorso.
Stima grossolana: ~3 h e ~120 g per set (Bambu Studio dà i valori esatti).

Verificato al computer con tutto il meccanismo degli occhi e la base. Nessuna interferenza con la slitta in alto,
a metà e in basso, con l'albero su e giù. Bulloni, rondelle e dadi sono liberi e appoggiano sul pieno. La guida
resta a 1.5 mm dal piede del supporto esterno. Il servo vero non è ancora stato provato.

Rigenerare pezzi e piatti: `python mechanical/mandibola/supporto_mandibola.py` (quote del servo in `SV`, della
slitta in `SL`, della guida, dei fori e della corsa in `GD`).
Il supporto precedente (traversa + braccio + culla, regolabile in 3 direzioni, appeso ai 2 fori Ø12) è sul ramo
`archivio`.
