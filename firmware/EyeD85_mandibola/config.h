// =====================================================================
//  EyeD85_mandibola — configurazione (unico file da toccare per tarare)
// =====================================================================
//  Come EyeD85_random (stessi valori degli occhi) + la MANDIBOLA:
//  Occhi EyeMech D85 (mechanical/eyes/eyemech_D85): 4 servo SG90/MG90S
//  e il servo grande della mandibola (DS3225, 25 kg) sulla stessa PCA9685,
//  comandata da un ESP8266 (ESP-12F).
//    mandibola: canale 0, 0 = chiusa, 1 = tutta aperta
//    X        : i due bulbi insieme, sinistra/destra
//    Y        : i due bulbi insieme, su/giu'
//    palpebre : un servo per occhio (superiore + inferiore insieme)
//
//  Convenzione dei valori (indipendente da come e' montato il servo):
//    X        : -1 = verso la sinistra di chi guarda gli occhi, 0 = davanti,
//               +1 = verso la destra di chi guarda
//    Y        : -1 = in basso, 0 = davanti, +1 = in alto
//    palpebre :  0 = chiuse, 1 = tutte aperte
//  La taratura e' in GRADI del servo, come nel codice di Will
//  (0..180 = 544..2400 us). I valori si trovano con lo sketch EyeD85_zero:
//  il suo comando 'p' stampa le righe CAL_* gia' pronte da incollare qui.
//  Se un asse va al contrario basta scambiare neg/pos.
// =====================================================================
#pragma once
#include <stdint.h>

// ---------------------------------------------------------------------
//  Hardware
// ---------------------------------------------------------------------
const uint8_t PIN_SDA = 4;                 // GPIO4 = D2 (NodeMCU, Wemos D1 mini)
const uint8_t PIN_SCL = 5;                 // GPIO5 = D1
const uint8_t PCA_ADDR = 0x40;             // indirizzo I2C della PCA9685 (default)
const float   PCA_OSC_HZ = 25000000.0f;    // oscillatore interno (tarare se il centro e' spostato)
const uint8_t CH_X = 4, CH_Y = 6, CH_LID_L = 10, CH_LID_R = 11;   // canali PCA9685 (0-based)
const float   US_0 = 544.0f, US_180 = 2400.0f;                    // gradi -> microsecondi

// ---------------------------------------------------------------------
//  Taratura (gradi del servo) = corsa massima usata. Provata sulla D85
//  montata (25/10/2026, con EyeD85_zero):
//    X : gradi bassi = occhi verso la sinistra di chi guarda; verso destra
//        si muove fino a 142 ma li' ronza contro il fermo (sequenza 't' di
//        EyeD85_zero), quindi 139; verso sinistra 54 (36 dal centro);
//    Y : 50 = sguardo in basso, libero; in alto a 130 tocca la base, a 124
//        e' libero da fermo ma nel movimento batte ancora, anche a 119
//        (il servo sfora con i pezzi pesanti): 53..109;
//    palpebre : 90 = chiuse (squadrette montate a 90 come Will), 80 gradi
//        di corsa fino ad aperte: sinistra 90 -> 170, destra 90 -> 10.
//  Restare DENTRO la corsa libera: un SG90 contro un fermo va in stallo,
//  assorbe ~0.7 A e scalda.
// ---------------------------------------------------------------------
struct AxisCal { float neg, mid, pos; };   // gradi a -1, 0, +1
struct LidCal  { float closed, open; };     // gradi a 0 e 1
const AxisCal CAL_X     = { 54.0f, 90.0f, 139.0f };
const AxisCal CAL_Y     = { 53.0f, 90.0f, 109.0f };
const LidCal  CAL_LID_L = { 90.0f, 170.0f };
const LidCal  CAL_LID_R = { 90.0f, 10.0f };

// ---------------------------------------------------------------------
//  Range del movimento (frazione della corsa tarata, 0..1): movimento
//  "teatrale", usa tutta la corsa. Per uno sguardo piu' naturale:
//  RANGE_X 0.9, RANGE_Y 0.7, EXTREME_PROB 0.
// ---------------------------------------------------------------------
const float RANGE_X = 1.00f;
const float RANGE_Y = 1.00f;
const float EXTREME_PROB = 0.40f;    // prob. di guardare verso un bordo o un angolo

// Palpebre a riposo e come seguono lo sguardo su/giu'
const float LID_OPEN_REST = 0.95f;   // apertura normale (occhi sgranati)
const float LID_LOOK_DOWN = 0.50f;   // guardando in basso scendono (fino a -0.50)
const float LID_LOOK_UP   = 0.10f;   // guardando in alto si aprono un po' di piu'
const float LID_REST_MIN  = 0.30f;

// ---------------------------------------------------------------------
//  Tempi (ms), poi moltiplicati per l'umore. SG90: ~0.1 s / 60 gradi a
//  5 V senza carico; i pezzi della D85 sono grandi, SPEED_SCALE li
//  rallenta tutti insieme.
// ---------------------------------------------------------------------
const uint16_t FIX_MIN_MS        = 250;   // quanto resta fermo a guardare un punto
const uint16_t FIX_MAX_MS        = 1600;
const uint16_t SACCADE_BASE_MS   = 120;   // spostamento rapido dello sguardo
const uint16_t SACCADE_PER_UNIT  = 180;   // + ms per ogni unita' di distanza
const float    NEW_POINT_PROB    = 0.80f; // prob. di un punto nuovo invece di un piccolo spostamento
const float    GLANCE_PROB       = 0.10f; // prob. di uno spostamento lento (scansione)
const uint16_t BLINK_MIN_MS      = 1500;  // intervallo tra battiti di ciglia
const uint16_t BLINK_MAX_MS      = 4500;
const uint16_t BLINK_CLOSE_MS    = 110;
const uint16_t BLINK_HOLD_MS     = 50;
const uint16_t BLINK_OPEN_MS     = 190;
const float    DOUBLE_BLINK_PROB = 0.15f;
const float    BLINK_AFTER_BIG   = 0.35f; // prob. di sbattere dopo un grande spostamento
const float    WINK_PROB         = 0.08f; // prob. che un battito sia un occhiolino
const uint16_t WINK_HOLD_MS      = 450;
const float    MICRO_AMP         = 0.05f; // micro-movimenti durante la fissazione (0 = off)
const uint32_t MOOD_MIN_MS       = 60000UL;   // l'umore cambia ogni 1-4 minuti
const uint32_t MOOD_MAX_MS       = 240000UL;

// Scala globale della velocita': < 1 per bulbi grandi/pesanti
const float SPEED_SCALE = 1.0f;

// Avvio: un servo alla volta (meno spunto sull'alimentazione)
const uint16_t ATTACH_STEP_MS = 250;

// ---------------------------------------------------------------------
//  MANDIBOLA: servo DS3225 (25 kg) sul canale 0 della PCA9685.
//  Il DS3225 vuole impulsi da 500 a 2500 us: sulla versione "180" sono
//  0..180 gradi, sulla versione "270" 0..270 (scritto sull'etichetta o
//  sulla scatola): in quel caso JAW_DEG_SPAN = 270.
//  Gradi: 0 = chiusa (squadretta montata col servo a 0 e la bocca chiusa),
//  60 = tutta aperta, da tarare insieme sulla testa (comando m<gradi>,
//  es. m45). "Chiusa" = denti che si toccano appena, NON oltre: un servo
//  da 25 kg che spinge contro il cranio va in stallo (2-3 A) e scalda.
// ---------------------------------------------------------------------
const uint8_t CH_JAW = 0;
const float   JAW_US_MIN = 500.0f, JAW_US_MAX = 2500.0f, JAW_DEG_SPAN = 180.0f;
struct JawCal { float closed, open; };     // gradi a 0 (chiusa) e 1 (tutta aperta)
const JawCal CAL_JAW = { 0.0f, 60.0f };    // DA TARARE (bocca da mostro: anche 70)
const float  JAW_MAX_TRAVEL = 90.0f;       // sicurezza: mai piu' di 90 gradi dalla chiusura (anche col comando m)

// Ritmo e velocita'
const uint16_t JAW_EVENT_MIN_MS = 2500;    // pausa tra un'azione e l'altra (poi x umore)
const uint16_t JAW_EVENT_MAX_MS = 9000;
const uint16_t JAW_FULL_MS      = 220;     // tempo minimo per TUTTA la corsa (DS3225: 0.16 s / 60
                                           // gradi a 5 V, a vuoto): piu' veloce sforza solo il servo
const float    JAW_REST         = 0.00f;   // apertura a riposo (0 = chiusa; 0.05 = un filo aperta)
const float    JAW_SYNC_EYES    = 1.0f;    // 1 = gli occhi reagiscono (sgranati col ruggito, palpebre
                                           // giu' con lo sbadiglio, niente battiti durante il ruggito);
                                           // 0 = occhi e mandibola indipendenti
