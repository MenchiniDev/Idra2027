// =====================================================================
//  EyeNode — configurazione (unico file da toccare per tarare le teste)
// =====================================================================
//  Lo stesso firmware va caricato su TUTTE le schede: ogni testa si
//  distingue dall'indirizzo impostato sul DIP switch (SW1) e da un seme
//  casuale diverso a ogni accensione. Nessuna sincronizzazione tra teste.
//
//  Convenzione dei valori (indipendente da come e' montato il servo):
//    sx/dx  : -1 = guarda a sinistra della testa, +1 = a destra
//    su/giu : -1 = guarda in basso,               +1 = in alto
//    palpebre: 0 = chiuse,                         1 = tutte aperte
//  Se un servo si muove al contrario basta scambiare neg e pos.
// =====================================================================
#pragma once
#include <stdint.h>

struct ServoCal { int16_t neg, mid, pos; };      // microsecondi a -1, 0, +1
struct LidCal   { int16_t closed, open; };        // microsecondi a 0 e 1
struct EyeCal   { ServoCal lr, ud; LidCal lid; };

// ---------------------------------------------------------------------
//  Teste: indirizzo DIP -> numero di occhi (2 = coppia, 1 = solo canali A)
//  Indice 0 = scheda senza indirizzo (DIP tutto OFF): trattata come coppia.
// ---------------------------------------------------------------------
const uint8_t MAX_ADDR = 4;
const uint8_t EYES_FOR_ADDR[MAX_ADDR + 1] = {
  2,   // 0000  (default / banco prova)
  2,   // 0001  Testa 1
  2,   // 0010  Testa 2
  2,   // 0011  Testa 3
  1,   // 0100  Testa 4 (occhio singolo)
};

// ---------------------------------------------------------------------
//  Calibrazione [indirizzo][occhio A, occhio B] — valori di partenza,
//  da rifinire sul carro con il comando seriale 'c' (centro) e i limiti
//  meccanici reali di ogni occhio. Restare DENTRO la corsa libera: un
//  servo che spinge contro un fermo va in stallo (~0.8 A) e scalda.
// ---------------------------------------------------------------------
#define CAL_DEFAULT_EYE { {1150, 1500, 1850}, {1250, 1500, 1750}, {1100, 1850} }
const EyeCal CAL[MAX_ADDR + 1][2] = {
  { CAL_DEFAULT_EYE, CAL_DEFAULT_EYE },   // 0
  { CAL_DEFAULT_EYE, CAL_DEFAULT_EYE },   // Testa 1
  { CAL_DEFAULT_EYE, CAL_DEFAULT_EYE },   // Testa 2
  { CAL_DEFAULT_EYE, CAL_DEFAULT_EYE },   // Testa 3
  { CAL_DEFAULT_EYE, CAL_DEFAULT_EYE },   // Testa 4 (B non usato)
};

// ---------------------------------------------------------------------
//  Range del movimento casuale (frazione della corsa calibrata, 0..1).
//  Ogni testa all'accensione sceglie a caso un proprio range dentro
//  [MIN, MAX], quindi alcune teste "esplorano" piu' di altre.
// ---------------------------------------------------------------------
const float RANGE_LR_MIN = 0.60f, RANGE_LR_MAX = 1.00f;
const float RANGE_UD_MIN = 0.45f, RANGE_UD_MAX = 0.85f;
const float BIAS_LR_MAX  = 0.25f;   // direzione "preferita" casuale di ogni testa
const float BIAS_UD_MAX  = 0.15f;

// ---------------------------------------------------------------------
//  Tempi (ms). Vengono poi moltiplicati per il carattere della testa e
//  per l'umore del momento, quindi sono valori medi, non fissi.
// ---------------------------------------------------------------------
const uint16_t FIX_MIN_MS        = 350;   // quanto resta fermo a guardare un punto
const uint16_t FIX_MAX_MS        = 2600;
const uint16_t SACCADE_BASE_MS   = 110;   // spostamento rapido dello sguardo
const uint16_t SACCADE_PER_UNIT  = 160;   // + ms per ogni unita' di distanza
const float    GLANCE_PROB       = 0.15f; // prob. di uno spostamento lento (scansione)
const uint16_t BLINK_MIN_MS      = 2500;  // intervallo tra battiti di ciglia
const uint16_t BLINK_MAX_MS      = 7500;
const uint16_t BLINK_CLOSE_MS    = 90;
const uint16_t BLINK_HOLD_MS     = 50;
const uint16_t BLINK_OPEN_MS     = 160;
const float    DOUBLE_BLINK_PROB = 0.15f;
const float    BLINK_AFTER_BIG   = 0.20f; // prob. di sbattere dopo un grande spostamento
const float    MICRO_AMP         = 0.03f; // micro-movimenti durante la fissazione (0 = off)
const float    LID_FOLLOW        = 0.25f; // le palpebre seguono lo sguardo su/giu'
const float    LID_REST_MIN      = 0.30f;
const uint32_t MOOD_MIN_MS       = 60000UL;   // l'umore cambia ogni 1–4 minuti
const uint32_t MOOD_MAX_MS       = 240000UL;

// Scala globale della velocita': < 1 per bulbi grandi/pesanti (D90 ~0.8)
const float SPEED_SCALE = 1.0f;

// ---------------------------------------------------------------------
//  Avvio scaglionato: i servo vengono agganciati uno alla volta e ogni
//  testa parte con un ritardo diverso (meno spunto sulla batteria).
// ---------------------------------------------------------------------
const uint16_t ATTACH_STEP_MS = 120;
const uint16_t START_DELAY_PER_ADDR_MS = 400;

// ---------------------------------------------------------------------
//  Monitor tensione servo (VSERVO su A7, partitore 1:2 sulla scheda)
// ---------------------------------------------------------------------
const float VSERVO_LOW = 4.4f;   // sotto questa soglia per 3 s -> umore "calmo" forzato

// ---------------------------------------------------------------------
//  Monitor batteria OPZIONALE su A6 (header AUX J11, pin 4).
//  Richiede un partitore esterno: +12V batteria -- 47k -- A6 -- 10k -- GND
//  (rapporto 5.7: 14.7 V -> 2.58 V). Senza partitore lasciare 0.
//  Soglie per 2 x 6 V piombo in serie, misurate SOTTO CARICO.
// ---------------------------------------------------------------------
#define BATT_SENSE_ENABLED 0
const float BATT_DIVIDER = 5.7f;
const float BATT_LOW     = 11.9f;  // -> umore "assonnato" forzato
const float BATT_CRIT    = 11.3f;  // per 10 s -> occhi chiusi e servo staccati
const float BATT_RESUME  = 12.4f;  // riparte solo sopra questa (isteresi)
