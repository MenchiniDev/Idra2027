# Firmware

| Sketch | Scheda | Uso |
|---|---|---|
| `EyeD85_random/` | ESP8266 (ESP-12F, NodeMCU) + PCA9685 | **movimento casuale degli occhi D85** (canali 4 = X, 6 = Y, 10/11 = palpebre); dettagli e taratura nel suo `README.md` |
| `EyeD85_mandibola/` | come sopra + **servo mandibola DS3225 sul canale 0** | come `EyeD85_random` più la **mandibola** che si muove a caso (morsi, ruggiti, sbadigli, borbottii, scatti); taratura `m45`, demo `n`; dettagli nel suo `README.md` |
| `EyeD85_zero/` | come sopra | tutti i servo a 90° per montare le squadrette; taratura via seriale (`p` stampa le righe `CAL_*` per `config.h`) |
| `EyeNode_random/` | Arduino Nano sulla scheda EyeNode | movimento casuale, uno sketch per tutte le teste (descritto qui sotto) |

Caricare EyeD85 su ESP8266: Arduino IDE (core esp8266 3.1.2), scheda **NodeMCU 1.0 (ESP-12E Module)**.

# EyeNode_random

Movimento **autonomo e casuale** degli occhi, uno sketch unico per tutte le teste.
Nessuna sincronizzazione: ogni testa vive per conto suo.

```
firmware/
  EyeNode_random/
    EyeNode_random.ino   logica (non serve toccarla)
    config.h             taratura: calibrazione servo, range, tempi, soglie
```

## Come rende diverse le teste
All'accensione ogni scheda calcola un **seme casuale** da: indirizzo DIP + contatore di accensioni
salvato in EEPROM + rumore degli ingressi analogici. Dal seme estrae il **carattere** della testa:

| Tratto | Range | Effetto |
|---|---|---|
| velocità | 0.80–1.25 × | quanto sono rapidi gli spostamenti |
| fissazione | 0.70–1.50 × | quanto resta a guardare un punto |
| battiti di ciglia | 0.70–1.40 × | frequenza |
| ampiezza sx/dx, su/giù | `RANGE_*_MIN…MAX` in `config.h` | quanto esplora |
| direzione preferita | ± `BIAS_*_MAX` | dove guarda "di solito" |
| curiosità | 0.25–0.60 | probabilità di grandi spostamenti invece di piccoli |
| convergenza (solo coppie) | 0–0.06 | occhi leggermente strabici verso l'interno |

Poi, ogni 1–4 minuti, cambia **umore**: *calmo* (lento, sguardo stretto), *curioso*, *agitato*
(rapido, fissazioni brevi, occhi sgranati), *assonnato* (palpebre basse, battiti lenti e lunghi).

Movimenti: fissazione con micro-movimenti → saccade (spostamento rapido con frenata finale), a volte
uno spostamento lento di "scansione"; battiti di ciglia casuali, a volte doppi, spesso dopo un grande
spostamento; le palpebre seguono lo sguardo (guardando in basso si abbassano un po').
I due occhi di una coppia guardano nello stesso punto, come occhi veri.

Quindi: due teste non fanno mai la stessa cosa, e la stessa testa a ogni accensione ha un carattere nuovo.

## Caricare il firmware
1. Arduino IDE → scheda **Arduino Nano**, processore **ATmega328P** (sui cloni economici: *Old Bootloader*).
2. Aprire `EyeNode_random/EyeNode_random.ino`, caricare. Librerie: solo `Servo` (inclusa nell'IDE).
3. Impostare il DIP della scheda (ON = 1): Testa 1 `0001`, Testa 2 `0010`, Testa 3 `0011`, Testa 4 `0100`.
   La Testa 4 (occhio singolo) usa solo le uscite A (D3, D5, D6).

Compilato e verificato: 13.4 KB flash (43 %), 713 B RAM (34 %).

## Taratura sul carro (una volta per testa)
1. Aprire il Monitor seriale a **115200**, inviare `c`: tutti i servo vanno al centro e le palpebre aperte.
   In questa posizione si montano squadrette, `LidCrank` e `HornExtender` (servo a 90°).
2. In `config.h`, tabella `CAL[indirizzo][occhio]`, per ogni servo impostare i microsecondi:
   - `lr`/`ud`: `{neg, mid, pos}` = posizione a −1 (sinistra/basso), centro, +1 (destra/alto);
   - `lid`: `{closed, open}`.
   Se un servo va al contrario, scambiare `neg` e `pos`. **Restare dentro la corsa libera**: un servo
   che spinge contro un fermo va in stallo, consuma ~0.8 A e scalda.
3. Ricaricare e inviare `r` per far ripartire il movimento casuale. `b` = battito di ciglia, `s` = stato
   (indirizzo, seme, carattere, umore, tensione servo).

Regolazioni utili in `config.h`:
- `RANGE_*` — ampiezza massima del movimento casuale;
- `FIX_*`, `BLINK_*` — ritmo di sguardi e battiti;
- `SPEED_SCALE` — rallentare tutto per i bulbi grandi (D90: ~0.8);
- `MICRO_AMP = 0` — elimina i micro-movimenti se i servo "ronzano".

## LED blu di stato (D12)
| Lampeggio | Significato |
|---|---|
| N lampi ogni 3 s | funzionamento normale, N = numero della testa |
| acceso fisso | modalità centro (`c`) |
| lampeggio rapido | tensione servo bassa (o batteria bassa, se misurata) |
| un lampo ogni 4 s | batteria scarica: occhi chiusi, servo staccati |

## Misura batteria (opzionale)
Per far "addormentare" la testa a batteria scarica: partitore **47 kΩ / 10 kΩ** dal +12 V al pin A6 del
connettore AUX (J11, pin 4), 10 kΩ verso GND; poi `#define BATT_SENSE_ENABLED 1` in `config.h`.
Soglie (piombo 12 V sotto carico): < 11.9 V umore assonnato, < 11.3 V per 10 s occhi chiusi e servo
staccati, riparte sopra 12.4 V. Non sostituisce il modulo LVD (la logica continua a consumare).

Il simulatore per PC (`firmware/sim/`) è sul ramo `archivio`.
