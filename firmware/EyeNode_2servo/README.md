# EyeNode_2servo — occhi a 2 servo (MG995)

Firmware per la coppia di occhi a 2 servo: **sx/dx** (i due bulbi insieme) e **palpebre** (le
palpebre dei due occhi insieme). Il su/giù è bloccato meccanicamente.
Stesso comportamento di `EyeNode_random` (fissazioni, saccadi, scansioni lente, battiti di ciglia
singoli/doppi, carattere casuale a ogni accensione, umore che cambia ogni 1–4 minuti), con tempi
allungati per gli MG995 e micro-movimenti spenti (gli MG995 economici hanno una zona morta larga).

## Due architetture, stesso sketch
In `config.h`:

| `CENTRAL_PCA9685` | Hardware | Cosa fa lo sketch |
|---|---|---|
| `0` (default) | un Arduino Nano per testa (scheda EyeNode) | muove 1 testa: sx/dx su **D3**, palpebre su **D5**; numero della testa dal DIP (A0–A3) |
| `1` | un solo Nano alla base + PCA9685 (SDA = A4, SCL = A5) | muove **4 teste**, ognuna indipendente; canali PCA in `PCA_CH` (default: testa 1 = 0/1, testa 2 = 2/3, …) |

Compilato per Nano (ATmega328P): `0` → 14.5 KB flash (47 %), 703 B RAM; `1` → 14.8 KB (48 %),
1.1 KB RAM. Librerie: solo quelle incluse nell'IDE (Servo / Wire, EEPROM).

## Caricare
Arduino IDE → scheda **Arduino Nano**, processore **ATmega328P** (cloni: *Old Bootloader*) → aprire
`EyeNode_2servo.ino` → Carica.

## Taratura (una volta per testa)
Monitor seriale a **115200**, fine riga "Newline".
1. `c` → sx/dx al centro, palpebre aperte. In questa posizione montare XHorn e LidCrank.
2. Trovare i limiti col comando manuale (non serve ricaricare):
   - `l1500`, `l1300`, `l1700` … → servo sx/dx a quel valore in µs: annotare **sinistra / centro / destra**;
   - `p1150`, `p1800` … → servo palpebre: annotare **chiuse / aperte**;
   - architettura 1: prima `h0`…`h3` per scegliere la testa.
   Restare dentro la corsa libera: un MG995 contro un fermo assorbe 1.5–2.5 A e scalda.
3. Scrivere i valori in `CAL[]` di `config.h` (`{ {sx, centro, dx}, {chiuse, aperte} }`), ricaricare.
   Se un servo va al contrario, scambiare i due estremi.
4. `r` → movimento casuale. `b` = battito, `s` = stato.

## Regolazioni utili (`config.h`)
- `RANGE_LR_*`, `BIAS_LR_MAX` — quanto esplora lo sguardo;
- `FIX_*`, `BLINK_*`, `SACCADE_*` — ritmo; `SPEED_SCALE` < 1 rallenta tutto;
- `HOLD_RELEASE_MS` — se gli MG995 ronzano/tremano da fermi, es. `1500`: il segnale sx/dx viene
  sospeso dopo 1.5 s di immobilità (il bulbo resta in posizione per attrito).

## LED di stato (D12)
N lampi ogni 3 s = numero della testa (architettura 1: 4 lampi); acceso fisso = modo centro/manuale;
lampeggio rapido = tensione servo bassa; lampeggio continuo veloce = PCA9685 non trovata.
