# Occhi animatronici — note di progetto

Due modelli di partenza (in `mechanical/eyes/original/`) e una versione in uso, in due taglie:

| Cartella | Cosa |
|---|---|
| `original/eyemech_e3.2/` | **EyeMech ε3.2** di Will Cogley (3MF, PDF di montaggio, codice, scheda). Base della versione in uso |
| `original/morganmanly/` | **Animatronic Eyes – Double and Single** di MorganManly (`single_v4`, `double_compact`). Da qui viene l'idea delle palpebre a 1 servo per occhio |
| `eyemech_D85/` | **versione in uso**: EyeMech ingrandito, occhi a 200 mm tra i centri (bulbo Ø85.3), palpebre a 1 servo per occhio, sedi dei servo 1:1 |
| `idra_version/` | **idra_version**: gli stessi pezzi nella scala di Will (bulbo Ø32, occhi a 75 mm), palpebre a 1 servo per occhio, base di Will tagliata a metà con spazio per un PCA9685, da stampare per prima per provare il meccanismo. File `idra_version_*.stl`, un piatto A1 pronto (≈ 4 h 26 min, 98 g) |

Generatore unico: `mechanical/scripts/generate_eyemech.py`.

## Versione EyeMech D85 — pezzi originali di Will, palpebre a 1 servo (4 servo SG90/MG90S)
File in `mechanical/eyes/eyemech_D85/`; in `print_A1/` gli stessi pezzi grandi già disposti sui
piatti della Bambu A1 (256 × 256).

![EyeMech D85](img/eyemech_D85.png)

Parte dai pezzi **originali** di EyeMech ε3.2 (`EyeMech e3.2 SG90 - A.3mf`, versione print-in-place,
sedi SG90 lettera A) e li ingrandisce tutti dello stesso fattore **s = 200/75 = 2.667**, scelto perché i centri degli occhi
siano a **200 mm** (in Will sono a 75 mm); il bulbo viene Ø85.3. Bulbi, base
con gli incastri, supporti a L, telaio centrale X/Y, palpebre e tiranti. Un incastro
a scatto ingrandito lavora con la stessa deformazione dell'originale; i giochi dei perni
print-in-place passano da ~0.2 a ~0.5 mm (stessa proporzione).

Cambia solo quello che non si può ingrandire o che riguarda le palpebre:

| Cosa | Come |
|---|---|
| Sedi dei servo | **1:1**, per SG90/MG90S veri (22.8 × 12.4 mm, orecchie 32.6 mm, fori a 27.8 mm), ricavate direttamente nei pezzi: le sedi ingrandite di Will sono riempite e dentro c'è la sede del servo vero, con l'albero sull'asse della squadretta e la faccia superiore alla stessa quota (i mozzi delle squadrette non cambiano). Base: 3 sedi (Y al centro, palpebre sx e dx), il servo entra **di fianco, dal lato della squadretta**, le orecchie appoggiano sulla faccia del blocco, 2 viti M2×8 autofilettanti. `XAxisA`: sede del servo X nel telaio, il servo entra **dall'alto** come in Will, orecchie sul piano, 2 viti M2×8. Cavo: canale sotto il fondo del corpo, esce dall'altra parte del blocco. Nella base la tasca del corpo è 2.5 mm più lunga dal lato dell'albero (`SEAT_EXTRA`). Niente gusci né fermi di Will |
| Box del `CoreY` (sopra il servo X) | in Will ha una piastra con la finestra del servo e sotto la cavità delle orecchie: ingranditi sarebbero 2.7 volte il servo. Riempiti, con la **finestra 1:1** attorno al servo vero; il riempimento appoggia 0.2 mm sopra le orecchie (le trattiene come nell'originale) e ha 2 fori per le teste delle viti M2 |
| Squadrette (palpebre, X, Y) | mozzo rifatto: codolo Ø10 che scende di 8.7 mm fino allo scanalato del servo vero, sede Ø4.75×3 a pressione + vite M2×12 |
| Palpebre | Will usa 2 servo per occhio. Resta solo il servo **anteriore** (quello della palpebra superiore, tirante corto originale). La sua squadretta ha un secondo braccio (r 35.1 mm, 58.8° avanti) con un perno, che lascia libero il mozzo (sede dello scanalato e foro della vite del codolo); il nuovo tirante `LinkB` (interasse 104.9 mm) porta il moto all'orecchia della palpebra inferiore ed è **stampato insieme alla palpebra inferiore**, col giunto print-in-place originale di Will sull'orecchia (perno biconico, lo stesso della palpebra superiore). Spingendo in avanti le due orecchie le palpebre si chiudono insieme |
| Servo posteriore | eliminato, con la sua squadretta e il tirante lungo. La sua sede ingrandita resta vuota |
| Base | **ridotta** a 388 × 80 × 67 mm: in Will teneva anche la scheda e i servo posteriori, qui deve solo tenere i supporti a L e i 3 servo. Resta la striscia y −38…−8 (quote 1:1) con le fessure dei supporti e i blocchi delle sedi (accorciati a 24 mm sotto le orecchie). Divisa a metà (x = 0), unita da 2 chiavette a coda di rondine sotto, con 2 viti M3×10 svasate ciascuna |
| Porta-PCB | non inclusi: ingranditi terrebbero una scheda di Will 2.7 volte più grande |

**Cinematica palpebre** (ottimizzata nello script): con 80° di corsa del servo la palpebra superiore fa
−35.5…+24.3° e l'inferiore +36.7…−21.4°: speculari entro 1°, come le due palpebre a servo separato
di Will (bordi a circa ±60° da aperte, a ~0° da chiuse). Gli angoli di trasmissione restano tra 54° e 90°.
Il `LinkB` parte dal lato esterno della squadretta (per non toccare il tirante originale vicino al giunto)
e rientra sul piano dell'orecchia a metà lunghezza, prima del supporto esterno. Vicino al giunto ha uno scarico
che lo tiene ad almeno 1.3 mm (0.5 mm di Will × s) dal bordo della palpebra su tutta la corsa.

**Verifica al computer**: nessuna interferenza tra palpebre, tiranti, squadretta, bulbo, supporti, base e
servo vero su tutta la corsa (da 4° oltre l'apertura fino a chiuse), anche tra `LinkB` e palpebra inferiore
(giunto print-in-place, con gioco). I gruppi print-in-place
modificati non si compenetrano. Il lato sinistro è lo specchio del destro.

**Assieme X/Y**: nel 3MF di Will `CoreY`, `XAxisA` e `XAxisB` sono solo in posa di stampa; lo script li
monta ricavando la posa dai vincoli (perni del `CoreY` sull'asse degli occhi, anelli di `XAxisA` sotto i
centri dei bulbi, servo X dentro il box del `CoreY`, squadretta di `XAxisB` sull'albero). Con questa posa
il mozzo della squadretta Y cade esattamente sull'asse degli alberi delle palpebre (z 11.2), e in posa
neutra non c'è nessuna interferenza oltre agli incastri a scatto voluti. Nell'immagine le ultime due viste
mostrano i 4 servo (blu) con il resto trasparente.

### Cosa stampare (D85)
| File | Q.tà | Note |
|---|---|---|
| `Base_L`, `Base_R` | 1+1 | 194 × 80 × 67 mm ciascuna, stanno insieme su un piatto. Contengono le sedi 1:1 dei servo Y e palpebre (la sede Y è a cavallo della giunzione) |
| `BaseKey_x2` | 2 | chiavette sotto la giunzione, viti M3×10 svasate (4) |
| `PivotCentral_x2`, `PivotOuter_L`, `PivotOuter_R` | 2+1+1 | supporti a L |
| `Eyeball_x2` | 2 | bulbi di Will Ø85.3 (pochi perimetri, riempimento basso: pieni sarebbero ~200 g) |
| `CoreY_PIP` | 1 | telaio su/giù + squadretta Y (print-in-place); nel box la finestra 1:1 del servo X |
| `XAxisA_PIP`, `XAxisB_PIP` | 1+1 | asse X (print-in-place), in `XAxisA` la sede 1:1 del servo X. Lunghi 264 mm: **in diagonale** sul piatto da 256 (già fatto in `print_A1/P2`, `P3`) |
| `LidTop_L_PIP`, `LidTop_R_PIP` | 1+1 | palpebra superiore + tirante originale + squadretta nuova (print-in-place) |
| `LidBottom_L_PIP`, `LidBottom_R_PIP` | 1+1 | palpebra inferiore + `LinkB` (print-in-place, giunto di Will sull'orecchia), 81 × 152 × 121 mm; il tratto obliquo del tirante va sostenuto |
| `PinB_x2` | 2 | perno del secondo braccio (testa sul piatto), vite M3×20 |

Orientamenti di stampa: quelli di Will (presi dal suo 3MF), solo ingranditi.
`print_A1/`: P1 = `Base_L` + `Base_R` + chiavette e perni, P2 = `XAxisA`, P3 = `XAxisB`.
`bambu_A1/`: tutti i pezzi già tagliati in Bambu Studio su 8 piatti A1 (PLA, 0.20 mm): **≈ 30 h 53 min e
≈ 0.87 kg di filamento** in totale; tempi e grammi per piatto in `bambu_A1/README.md`.

### Montaggio
Come nella guida di Will (`mechanical/eyes/original/eyemech_e3.2/src/Assembly.pdf`), con queste differenze:
1. Servo X: dall'alto nella sede di `XAxisA` (cavo verso la tacca), 2 viti M2×8, poi si aggancia il `CoreY` sopra.
   Servo Y e palpebre: si infilano nella base **prima** di `PivotCentral` / `PivotOuter`, di fianco dal lato
   della squadretta, col cavo infilato prima nel canale sotto il corpo; 2 viti M2×8 nelle orecchie.
2. Palpebre: montare solo il servo anteriore di ogni lato (quello che Will chiama TOP LEFT / TOP RIGHT).
   La sede del servo posteriore resta vuota.
3. `LinkB`: arriva già montato sulla palpebra inferiore (giunto print-in-place: sbloccarlo a mano dopo la
   stampa, niente rondella né vite sull'orecchia); il suo anello esterno va sul `PinB` (codolo nel foro del
   secondo braccio, vite M3×20 dall'esterno).
4. Base: unire le due metà con le chiavette prima di montare il resto.

**Calibrazione**: come Will, servo a 90° = palpebre chiuse. Aperte: destra 90° → 10°, sinistra
90° → 170° (i canali TR/TL del suo codice; BR/BL non servono più). Il firmware deve gestire 4 servo
(`EyeNode_2servo` ne gestisce 2).

### Da verificare
- **Misure SG90** (`SG_*` e `SG_SPLINE_TOP`/`SG_BOSS_TOP` nello script, stimate da datasheet): provare
  una sede e una squadretta con un servo vero prima del resto.
- **Sedi X e Y**: le sedi di palpebre e Y prendono l'asse dal mozzo della loro squadretta; il servo X sta
  nella finestra di `XAxisA` (25.6 mm per un corpo di 22.8) a 0.75 mm dal lato posteriore, così il telaio
  laterale di `XAxisB` passa dietro le orecchie dei servo palpebre. Controllare al montaggio che i codoli
  delle squadrette non tocchino il mozzo ingranaggi.
- **Coppia**: i pezzi sono 2.7 volte più grandi e circa 19 volte più pesanti dell'originale. Gli
  **MG90S** sono consigliati (stesse sedi), soprattutto per palpebre e Y; stampare palpebre e bulbi leggeri.

## idra_version — stessi pezzi, scala di Will (versione di prova)
File in `mechanical/eyes/idra_version/` (`idra_version_*.stl`). Da stampare **prima** della D85: costa poco filamento e
qualche ora, e fa vedere se il meccanismo funziona davvero.

![idra_version](img/idra_version.png)

È la D85 senza l'ingrandimento (s = 1): bulbo Ø32, occhi a 75 mm, base in un pezzo solo.
Siccome la scala è quella di Will, **squadrette, telaio X, box del `CoreY` e sedi dei servo sono i suoi originali**
(gli SG90/MG90S ci entrano come nel suo progetto, tenuti dai suoi fermi). **Base**: quella di Will **tagliata a
y = −7** (`CUT_Y`), subito dietro il dente che fa da battuta ai servo anteriori delle palpebre e dietro i piedi
dei supporti a L: via le sedi dei servo posteriori e i porta-PCB. Dietro il taglio, al centro, una **linguetta
piatta per un PCA9685** (62.5 × 25.4 mm) con 4 distanziali alti 5 mm e fori per viti M2.5 autofilettanti a
55.9 × 19.0 mm (`PCA` nello script: **verificare l'interasse sulla propria scheda**). Ingombro 145 × 69 mm (l'originale
è 145 × 95). **Fermi**: `Retainer_Single` di Will per il servo Y (le sue fessure restano); per le palpebre il fermo
doppio di Will (servo anteriore + posteriore) diventa `Retainer_Lid`: gamba anteriore e arco sopra il servo
anteriore come in Will, e gamba posteriore speculare che si aggancia sotto il bordo del taglio, con lo stesso gioco
(0.08 mm). **Lunghezza delle sedi**: tra il fondo del vassoio e l'arco del fermo Will lascia al corpo del servo
23.0 mm (palpebre) e 23.15 mm (Y), meno della tasca da 23.3 mm della base ridotta, che con i servo veri era corta
di 1–2 mm: l'arco di tutti e tre i fermi è alzato di 2.5 mm (`RET_LIFT`, gambe più lunghe; denti e fessure
restano), quindi 25.5 e 25.65 mm. Dall'albero (sull'asse della squadretta) il fondo è a 16.6 mm e l'arco a
8.9 mm. **Zona ribassata** dei servo palpebre (dove entra l'estremità inferiore del servo, profonda 2.25 mm):
in Will lascia 0.3 mm tra il fondo del servo e la parete verso il centro; allungata di 2.5 mm verso il centro
(`POCKET_EXTRA`, ora da x = ±25.1), larghezza e profondità invariate. Quella del servo Y ha già ~2 mm di margine.
Disegni: `img/idra_version_zona_ribassata.png`, `img/idra_version_fermi.png`. La versione precedente, base ridotta a una striscia con blocchi nuovi e senza fermi, non teneva i servo.
**Palpebre**: un servo per occhio, squadretta a V
(braccio di Will + secondo braccio col `PinB`) con il **mozzo originale di Will libero**: sede dello scanalato
profonda 2.6 mm, così entra fino in fondo, e foro passante Ø2.6 per la vite. Il `LinkB` è **stampato insieme alla
palpebra inferiore** con il giunto print-in-place originale di Will sull'orecchia (perno biconico, lo stesso della
palpebra superiore); vicino al giunto ha uno scarico che lo tiene ad almeno 0.5 mm dal bordo della palpebra su
tutta la corsa. Cinematica identica alla D85 (stessi angoli, interasse `LinkB` 39.3 mm). I pezzi nuovi hanno quote
ridotte a circa 3/8 e **viti M2** (`DIM["small"]` nello script).

**Cosa prova**: movimento delle palpebre a un servo (secondo braccio + `LinkB`), print-in-place,
assi X/Y, montaggio e firmware a 4 servo.
**Cosa non prova**: i mozzi rifatti, il telaio X e il box del `CoreY` della D85 (qui sono quelli di Will), le sedi
1:1 dei servo della D85 e il peso dei pezzi grandi.

### Cosa stampare (idra_version)
| File | Q.tà | Note |
|---|---|---|
| `Base` | 1 | base di Will tagliata + linguetta PCA9685, 145 × 69 × 16 mm |
| `Retainer_Single`, `Retainer_Lid_x2` | 1+2 | fermi: servo Y (di Will), servo palpebre (fermo doppio di Will accorciato), arco alzato di 2.5 mm |
| `PivotCentral_x2`, `PivotOuter_L`, `PivotOuter_R` | 2+1+1 | supporti a L |
| `Eyeball_x2` | 2 | bulbi di Will Ø32 |
| `CoreY_PIP`, `XAxisA_PIP`, `XAxisB_PIP` | 1+1+1 | assi X/Y di Will (print-in-place) |
| `LidTop_L_PIP`, `LidTop_R_PIP` | 1+1 | palpebra superiore + tirante + squadretta a V (col secondo braccio) |
| `LidBottom_L_PIP`, `LidBottom_R_PIP` | 1+1 | palpebra inferiore + `LinkB` (print-in-place; il tratto del tirante sull'orecchia va sostenuto) |
| `PinB_x2` | 2 | pezzi piccoli (Ø9): ugello 0.4, layer 0.12–0.16 |

**Stampa** (`idra_version/bambu_A1/`): tutti i 19 pezzi su **un solo piatto A1**, già tagliato: **≈ 4 h 26 min e ≈ 98 g** di PLA
(disposizione in `img/idra_version_piatto.png`; `mechanical/scripts/pack_plate.py` la rifà).

Viti: per lato 1 × M2×8 nel `PinB` (si filetta nel braccio); 4 × M2.5×6 autofilettanti per il PCA9685; il resto
come nella guida di Will, compresa la vite della squadretta a V nel foro del mozzo. Montaggio: guida di Will + punto 2 della D85 (servo posteriore non montato);
il `LinkB` arriva già montato sulla palpebra inferiore (sbloccare il giunto a mano dopo la stampa), il suo anello
esterno va sul `PinB` (codolo nel foro del secondo braccio, vite M2×8 dall'esterno).

## Rigenerare
```bash
pip install trimesh manifold3d numpy scipy shapely pyvista
python mechanical/scripts/generate_eyemech.py                       # D85: occhi a 200 mm (bulbo 85.3) + print_A1, con verifica
python mechanical/scripts/generate_eyemech.py --small               # versione di prova in scala di Will
python mechanical/scripts/generate_eyemech.py --interasse 210       # altra distanza tra i centri degli occhi
python mechanical/scripts/generate_eyemech.py --interasse 0 --d 90  # scala dal diametro del bulbo
python mechanical/scripts/generate_eyemech.py --render              # immagine in docs/img
```

## Licenza
Entrambi i modelli di partenza sono **CC BY-NC-SA 4.0** (attribuzione, **non commerciale**, condividi
allo stesso modo) e i file derivati qui sono soggetti alla stessa licenza. Un carro allegorico ha un
contesto commerciale/professionale: tutti i pezzi della versione in uso derivano da EyeMech ε3.2, quindi
per il carro serve il permesso di **Will Cogley** (enquiries@willcogley.com); l'idea delle palpebre
a 1 servo viene da MorganManly.
