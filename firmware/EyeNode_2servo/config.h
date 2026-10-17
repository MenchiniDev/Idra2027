// =====================================================================
//  EyeNode_2servo — configurazione (unico file da toccare per tarare)
// =====================================================================
//  Ogni testa ha 2 servo (MG995):
//    sx/dx    : i due bulbi girano insieme (squadretta doppia XHorn)
//    palpebre : le palpebre dei due occhi insieme (barra LidBail)
//  Il su/giu' e' bloccato meccanicamente.
//
//  Convenzione dei valori (indipendente da come e' montato il servo):
//    sx/dx    : -1 = guarda a sinistra della testa, 0 = davanti, +1 = a destra
//    palpebre :  0 = chiuse, 1 = tutte aperte
//  Se un servo si muove al contrario basta scambiare neg/pos (o closed/open).
// =====================================================================
#pragma once
#include <stdint.h>

// ---------------------------------------------------------------------
//  ARCHITETTURA
//    0 = un Arduino Nano per testa (scheda EyeNode), servo sui pin del Nano,
//        indirizzo della testa dal DIP switch (A0..A3).
//    1 = un solo Arduino Nano alla base che muove TUTTE le teste tramite
//        una scheda PCA9685 (I2C su A4 = SDA, A5 = SCL).
// ---------------------------------------------------------------------
#define CENTRAL_PCA9685 0

struct ServoCal { int16_t neg, mid, pos; };   // microsecondi a -1, 0, +1
struct LidCal   { int16_t closed, open; };     // microsecondi a 0 e 1
struct HeadCal  { ServoCal lr; LidCal lid; };

// ---------------------------------------------------------------------
//  Teste. Indice = indirizzo DIP (architettura 0) oppure numero testa
//  (architettura 1). Indice 0 = banco prova / scheda senza indirizzo.
//  Valori di partenza: rifinirli sul carro con il comando seriale 'c'
//  (centro) e i comandi manuali ('l', 'p', vedi README).
//  Restare DENTRO la corsa libera: un MG995 che spinge contro un fermo
//  assorbe 1.5-2.5 A e scalda.
// ---------------------------------------------------------------------
const uint8_t MAX_HEAD = 4;
#define CAL_DEFAULT_HEAD { {1200, 1500, 1800}, {1150, 1800} }
const HeadCal CAL[MAX_HEAD + 1] = {
  CAL_DEFAULT_HEAD,   // 0  banco prova
  CAL_DEFAULT_HEAD,   // 1  Testa 1
  CAL_DEFAULT_HEAD,   // 2  Testa 2
  CAL_DEFAULT_HEAD,   // 3  Testa 3
  CAL_DEFAULT_HEAD,   // 4  Testa 4
};

// Pin dei servo nell'architettura 0 (uscite A1/A2 della scheda EyeNode)
const uint8_t PIN_LR  = 3;
const uint8_t PIN_LID = 5;

// Architettura 1: teste gestite e canali PCA9685 [sx/dx, palpebre] di ognuna
const uint8_t N_HEADS_CENTRAL = 4;
const uint8_t PCA_CH[N_HEADS_CENTRAL][2] = { {0, 1}, {2, 3}, {4, 5}, {6, 7} };
const uint8_t PCA_ADDR = 0x40;            // indirizzo I2C della PCA9685 (default)
const float   PCA_OSC_HZ = 25000000.0f;   // oscillatore interno (tarare se il centro e' spostato)

// ---------------------------------------------------------------------
//  Range del movimento casuale (frazione della corsa calibrata, 0..1).
//  Ogni testa all'accensione sceglie a caso il proprio range in [MIN, MAX].
// ---------------------------------------------------------------------
const float RANGE_LR_MIN = 0.60f, RANGE_LR_MAX = 1.00f;
const float BIAS_LR_MAX  = 0.25f;   // direzione "preferita" casuale di ogni testa

// ---------------------------------------------------------------------
//  Tempi (ms), poi moltiplicati per carattere e umore della testa.
//  Gli MG995 sono piu' lenti degli MG90S (~0.17 s / 60 gradi a 6 V): i
//  tempi sono gia' allungati, scendere sotto vuol dire chiedere al servo
//  una velocita' che non ha (non si rompe, ma il movimento e' meno fluido).
// ---------------------------------------------------------------------
const uint16_t FIX_MIN_MS        = 500;   // quanto resta fermo a guardare un punto
const uint16_t FIX_MAX_MS        = 3200;
const uint16_t SACCADE_BASE_MS   = 180;   // spostamento rapido dello sguardo
const uint16_t SACCADE_PER_UNIT  = 260;   // + ms per ogni unita' di distanza
const float    GLANCE_PROB       = 0.18f; // prob. di uno spostamento lento (scansione)
const uint16_t BLINK_MIN_MS      = 2500;  // intervallo tra battiti di ciglia
const uint16_t BLINK_MAX_MS      = 7500;
const uint16_t BLINK_CLOSE_MS    = 170;
const uint16_t BLINK_HOLD_MS     = 60;
const uint16_t BLINK_OPEN_MS     = 260;
const float    DOUBLE_BLINK_PROB = 0.15f;
const float    BLINK_AFTER_BIG   = 0.25f; // prob. di sbattere dopo un grande spostamento
const float    MICRO_AMP         = 0.0f;  // micro-movimenti (MG995: zona morta larga -> off)
const float    LID_REST_MIN      = 0.30f;
const uint32_t MOOD_MIN_MS       = 60000UL;   // l'umore cambia ogni 1-4 minuti
const uint32_t MOOD_MAX_MS       = 240000UL;

// Scala globale della velocita': < 1 per bulbi grandi/pesanti
const float SPEED_SCALE = 1.0f;

// ---------------------------------------------------------------------
//  Riposo dei servo: da fermi gli MG995 economici "cacciano" (ronzano e
//  tremano). Se HOLD_RELEASE_MS > 0, dopo quel tempo di immobilita' il
//  segnale del servo sx/dx viene sospeso finche' non deve muoversi di
//  nuovo (il bulbo resta dov'e' per attrito). 0 = sempre agganciato.
// ---------------------------------------------------------------------
const uint16_t HOLD_RELEASE_MS = 0;

// ---------------------------------------------------------------------
//  Avvio scaglionato (meno spunto sulla batteria)
// ---------------------------------------------------------------------
const uint16_t ATTACH_STEP_MS = 150;
const uint16_t START_DELAY_PER_HEAD_MS = 400;

// ---------------------------------------------------------------------
//  Monitor tensione servo (architettura 0: VSERVO su A7, partitore 1:2)
// ---------------------------------------------------------------------
#define VSERVO_SENSE_ENABLED 1
const float VSERVO_LOW = 4.4f;   // sotto questa soglia per 3 s -> umore "calmo" forzato
