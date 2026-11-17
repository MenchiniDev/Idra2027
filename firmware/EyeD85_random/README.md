#line 1 "C:\\Users\\loren\\Desktop\\Idra2027\\firmware\\EyeD85_random\\README.md"
# EyeD85 — occhi EyeMech D85 a 4 servo (ESP8266 + PCA9685)

Firmware per gli occhi di `mechanical/eyes/eyemech_D85/`: 4 servo SG90/MG90S su una PCA9685,
comandata da una scheda con modulo **ESP-12F** (ESP8266, tipo NodeMCU o Wemos D1 mini).

| Sketch | A cosa serve |
|---|---|
| `EyeD85_zero/` | porta **tutti i servo a 90°** (posizione di montaggio delle squadrette: occhi dritti, palpebre chiuse) e permette di muovere un servo alla volta dal Monitor seriale per trovare i limiti |
| `EyeD85_random/` | **movimento "teatrale"**: usa tutta la corsa tarata, guarda spesso verso bordi e angoli; fissazioni brevi con micro-movimenti, saccadi, scansioni lente, palpebre che seguono lo sguardo, battiti singoli/doppi, occhiolini, umore che cambia ogni 1–4 minuti. Taratura e range in `config.h` |

Librerie: solo `Wire` (inclusa nel core). La PCA9685 è comandata con lo stesso driver minimo di
`EyeNode_2servo`. Compilati per NodeMCU 1.0: 244 KB / 247 KB di flash (23 %), RAM 36 % (quasi tutta
del core ESP8266). Il WiFi è spento.

## Collegamenti
| PCA9685 | Scheda ESP8266 |
|---|---|
| VCC | **3V3** (logica a 3.3 V: le resistenze di pull-up I2C della scheda vanno a VCC) |
| GND | GND |
| SDA | **D2** (GPIO4) |
| SCL | **D1** (GPIO5) |
| OE | non collegato |
| V+ (morsetto) | alimentatore **esterno 5–6 V, almeno 3 A**, GND in comune |

Canali (numerati da 0, come stampati sulla scheda):

| Canale | Servo |
|---|---|
| 4 | X — i due bulbi sinistra/destra |
| 6 | Y — i due bulbi su/giù |
| 10 | palpebre occhio sinistro |
| 11 | palpebre occhio destro |

Non alimentare i servo dal 5 V/VIN della scheda ESP (USB): allo spunto la scheda si resetta.
Un condensatore da 470–1000 µF sul V+ della PCA9685 aiuta. Per lo sguardo, sinistra/destra sono quelle
**di chi guarda gli occhi da davanti** (sulla D85: gradi bassi del servo X = sinistra).

## Arduino IDE
Su questo PC è già pronto: Arduino IDE 2 (installato con winget, si apre col comando `Arduino IDE` o dal
menu Start) con il core **esp8266 3.1.2**. Su un altro PC:
1. File → Preferenze → *URL aggiuntive per il gestore schede*:
   `https://arduino.esp8266.com/stable/package_esp8266com_index.json`
2. Strumenti → Scheda → Gestore schede → **esp8266** (ESP8266 Community) → Installa.
3. Scheda **NodeMCU 1.0 (ESP-12E Module)** (va bene per l'ESP-12F, 4 MB), porta del CH340 (qui **COM4**).
4. Aprire lo sketch → Carica. Monitor seriale a **115200**.

Da riga di comando, con lo stesso `arduino-cli` che l'IDE usa internamente (non è nel PATH: sta nella
cartella dell'IDE, in `resources/app/lib/backend/resources/arduino-cli.exe`; configurazione in
`%USERPROFILE%\.arduinoIDE\arduino-cli.yaml`, da passare con `--config-file`):
```bash
arduino-cli compile -b esp8266:esp8266:nodemcuv2 firmware/EyeD85_random
arduino-cli upload  -b esp8266:esp8266:nodemcuv2 -p COM4 firmware/EyeD85_random
```

## Taratura (una volta, a meccanica montata)
1. Caricare `EyeD85_zero`, accendere l'alimentazione dei servo: vanno a 90° uno alla volta.
   In questa posizione montare le squadrette (`docs/mechanical_eyes.md` → Montaggio, punto 0):
   X e Y con gli occhi dritti davanti, palpebre chiuse.
2. Monitor seriale a 115200, un comando per riga:
   - `x`, `y`, `s`, `d` selezionano il servo (X, Y, palpebre Sinistra, palpebre Destra);
   - `+` / `-` lo spostano di 1° (`++` / `--` di 5°), `x75` lo porta a 75° (decimali ammessi);
   - trovato un estremo, `1` lo memorizza come −1 (sinistra / basso / palpebre **chiuse**), `2` come centro
     (solo X e Y), `3` come +1 (destra / alto / palpebre **aperte**);
   - `t130,136,142` fa passare il servo selezionato per quei valori, 1 s ciascuno, andata e ritorno
     senza fine (qualsiasi altro comando la ferma): utile per vedere dove smette di muoversi;
   - `p` stampa le righe `CAL_*` già pronte; `z` riporta tutto a 90°; `o` spegne gli impulsi (servo liberi);
     `?` stato.

   Avvicinarsi ai fermi piano e **tornare indietro di 3–5°**: un SG90 che spinge contro un fermo va in
   stallo, assorbe ~0.7 A e scalda. Per le palpebre "chiuse" è il punto in cui i bordi si toccano appena.
3. Incollare le righe di `p` in `EyeD85_random/config.h` (al posto delle `CAL_*`), caricare `EyeD85_random`.
4. Comandi di `EyeD85_random`: `c` sguardo al centro tarato e palpebre tutte aperte (per controllare la
   taratura), `r` riprende il movimento, `b` battito, `w` occhiolino, `s` stato.
   **Pose ferme** per vedere il range, come sul tastierino numerico visto da chi guarda gli occhi:
   `6` tutto a destra, `4` a sinistra, `8` in alto, `2` in basso, `7` `9` `1` `3` gli angoli, `5` centro
   (palpebre aperte, scrive i gradi usati); `r` per ripartire.

I gradi sono quelli del codice di Will (0…180° = 544…2400 µs), quindi i suoi valori valgono anche qui.
L'oscillatore della PCA9685 varia da scheda a scheda di qualche %: se si cambia scheda, ricontrollare.

## Range (`config.h`)
X e Y provati sulla D85 montata (25/10/2026); le palpebre vengono dalla meccanica (angoli di Will, che non
cambiano con la scala).

| Servo | Taratura | Perché |
|---|---|---|
| X | 54 / 90 / 139° | gradi bassi = occhi verso la sinistra di chi guarda. Verso destra si muove fino a 142°, ma lì ronza contro il fermo: 139° |
| Y | 53 / 90 / 109° | 50° = sguardo in basso, libero; in alto a 130° tocca la base, a 124° è libero da fermo ma nel movimento batte ancora, anche a 119° (il servo sfora con i pezzi pesanti): in alto 109° |
| palpebre sx | 90 → 170° | 90° = chiuse (montaggio come Will), 80° di corsa (superiore −35.5…+24.3°, inferiore +36.7…−21.4°) |
| palpebre dx | 90 → 10° | speculare |

Il movimento usa **tutta la corsa tarata** (`RANGE_X = RANGE_Y = 1.0`) e nel 40 % degli spostamenti va verso
un bordo o un angolo (`EXTREME_PROB`); fissazioni brevi (0.25–1.6 s), battiti ogni 1.5–4.5 s, palpebre a
riposo al 95 % (`LID_OPEN_REST`, occhi sgranati) che scendono fino a −50 % guardando in basso
(`LID_LOOK_DOWN`). Con un solo servo per occhio superiore e inferiore si muovono insieme. Per uno sguardo
più naturale: `RANGE_X = 0.9`, `RANGE_Y = 0.7`, `EXTREME_PROB = 0`. Altre regolazioni: `FIX_*`,
`SACCADE_*`, `BLINK_*` (ritmo), `WINK_PROB` (occhiolini), `MICRO_AMP = 0` se i servo ronzano da fermi,
`SPEED_SCALE` < 1 per rallentare tutto (pezzi pesanti).

## LED del modulo
`EyeD85_random`: un lampo ogni 3 s = movimento casuale; acceso fisso = modo centro; lampeggio rapido =
PCA9685 non trovata (entrambi gli sketch riprovano ogni 2 s, basta collegarla).
