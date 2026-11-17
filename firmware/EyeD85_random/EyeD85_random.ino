// =====================================================================
//  EyeD85_random — movimento naturale degli occhi EyeMech D85
// =====================================================================
//  Scheda: ESP8266 (modulo ESP-12F, es. NodeMCU o Wemos D1 mini) con una
//  PCA9685 su I2C. 4 servo: X e Y muovono insieme i due bulbi, ogni occhio
//  ha il suo servo palpebre (superiore + inferiore insieme).
//  Taratura e range in config.h (valori trovati con EyeD85_zero).
//
//  Comportamento (come EyeNode_random, per una sola testa, ma "teatrale":
//  usa tutta la corsa tarata e guarda spesso verso bordi e angoli):
//    fissazione di un punto con micro-movimenti -> saccade verso un nuovo
//    punto (a volte uno spostamento lento di scansione); le palpebre
//    seguono lo sguardo (guardando in basso si abbassano); battiti di
//    ciglia casuali, a volte doppi, spesso dopo un grande spostamento,
//    ogni tanto un occhiolino; "umore" che cambia ogni 1-4 minuti
//    (calmo, curioso, agitato, assonnato).
//
//  Seriale 115200, comandi di una lettera:
//    c   sguardo al centro tarato, palpebre tutte aperte (verifica taratura)
//    1-9 sguardo fermo a un estremo della taratura, come sul tastierino
//        numerico visto da chi guarda gli occhi: 6 = tutto a destra,
//        4 = a sinistra, 8 = in alto, 2 = in basso, 7 9 1 3 = angoli,
//        5 = centro; palpebre tutte aperte
//    r   riprende il movimento casuale
//    b   battito di ciglia
//    w   occhiolino (alterna sinistra/destra)
//    s   stato
//
//  Librerie: solo Wire (inclusa nel core).
// =====================================================================
#include <Wire.h>
#include <math.h>
#if defined(ESP8266)
  #include <ESP8266WiFi.h>
#endif
#include "config.h"

const uint16_t UPDATE_MS = 10;
const uint8_t LID_L = 1, LID_R = 2, LID_BOTH = 3;    // maschera delle palpebre che sbattono

enum Mode { MODE_RANDOM, MODE_HOLD };

// ----------------------------------------------------------- utilita'
static float frand(float a, float b) { return a + (b - a) * (random(0, 10001) / 10000.0f); }
static bool chance(float p) { return random(0, 10000) < (long)(p * 10000.0f); }
static float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }
static float easeOutCubic(float t) { t = 1.0f - t; return 1.0f - t * t * t; }
static float easeInOutCubic(float t) {
  if (t < 0.5f) return 4.0f * t * t * t;
  float u = -2.0f * t + 2.0f;
  return 1.0f - u * u * u / 2.0f;
}

// Movimento interpolato da 'from' a 'to' in 'dur' ms
struct Move {
  float from = 0, to = 0, cur = 0;
  uint32_t t0 = 0;
  uint16_t dur = 0;
  bool smooth = false;     // false = saccade (parte veloce), true = lento in/out
  void go(float target, uint16_t ms, bool sm, uint32_t now) {
    from = cur; to = target; t0 = now; dur = ms; smooth = sm;
    if (ms == 0) cur = to;
  }
  bool done(uint32_t now) const { return dur == 0 || now - t0 >= dur; }
  void update(uint32_t now) {
    if (done(now)) { cur = to; return; }
    float t = (now - t0) / (float)dur;
    cur = from + (to - from) * (smooth ? easeInOutCubic(t) : easeOutCubic(t));
  }
};

// ----------------------------------------------------------- umori
struct Mood { const char *name; float fix, speed, range, blink, lid; uint8_t weight; };
const Mood MOODS[] = {
  // nome        fissaz. veloc. ampiezza battiti palpebre peso
  { "calmo",     1.3f,   0.85f, 0.85f,   1.20f,  0.00f,   15 },
  { "curioso",   1.0f,   1.00f, 1.00f,   1.00f,  0.05f,   40 },
  { "agitato",   0.45f,  1.25f, 1.00f,   0.60f,  0.10f,   35 },
  { "assonnato", 1.6f,   0.65f, 0.75f,   1.60f, -0.35f,   10 },
};
const uint8_t MOOD_SLEEPY = 3, N_MOODS = sizeof(MOODS) / sizeof(MOODS[0]);

// ----------------------------------------------------------- PCA9685
// Driver minimo (come EyeNode_2servo), senza librerie esterne
float pcaHz = 50.0f;
void pcaWrite8(uint8_t reg, uint8_t v) {
  Wire.beginTransmission(PCA_ADDR); Wire.write(reg); Wire.write(v); Wire.endTransmission();
}
bool pcaBegin() {
#if defined(ESP8266) || defined(ESP32)
  Wire.begin(PIN_SDA, PIN_SCL);
#else
  Wire.begin();
#endif
  Wire.setClock(100000);
  Wire.beginTransmission(PCA_ADDR);
  if (Wire.endTransmission() != 0) return false;
  uint8_t pre = (uint8_t)(PCA_OSC_HZ / (4096.0f * 50.0f) + 0.5f) - 1;
  pcaHz = PCA_OSC_HZ / (4096.0f * (pre + 1));
  pcaWrite8(0x00, 0x10);                     // MODE1: sleep (per cambiare prescaler)
  pcaWrite8(0xFE, pre);                      // PRE_SCALE
  pcaWrite8(0x00, 0x20);                     // MODE1: sveglia + auto-incremento
  delay(1);
  pcaWrite8(0x00, 0xA0);                     // restart
  pcaWrite8(0x01, 0x04);                     // MODE2: uscite totem-pole
  return true;
}
void pcaChannel(uint8_t ch, uint16_t on, uint16_t off) {
  Wire.beginTransmission(PCA_ADDR);
  Wire.write(0x06 + 4 * ch);
  Wire.write(on & 0xFF); Wire.write(on >> 8); Wire.write(off & 0xFF); Wire.write(off >> 8);
  Wire.endTransmission();
}

struct Out {                       // un canale della PCA9685, comandato in gradi
  uint8_t ch = 0;
  int lastTicks = -1;
  float deg = 90;
  void write(float d) {
    deg = clampf(d, 0.0f, 180.0f);
    float us = US_0 + (US_180 - US_0) * deg / 180.0f;
    int ticks = (int)(us * 4096.0f * pcaHz / 1000000.0f + 0.5f);
    if (ticks == lastTicks) return;
    lastTicks = ticks;
    pcaChannel(ch, 0, ticks);
  }
};

static float axisDeg(const AxisCal &c, float v) {
  v = clampf(v, -1.0f, 1.0f);
  return v >= 0 ? c.mid + (c.pos - c.mid) * v : c.mid + (c.mid - c.neg) * v;
}
static float lidDeg(const LidCal &c, float v) {
  return c.closed + (c.open - c.closed) * clampf(v, 0.0f, 1.0f);
}

// ----------------------------------------------------------- stato
Out outX, outY, outLidL, outLidR;
Mode mode = MODE_RANDOM;
uint8_t mood = 1;
Move gazeX, gazeY, lid;
float fixX = 0, fixY = 0, microX = 0, microY = 0, lidLevel = LID_OPEN_REST;
float holdX = 0, holdY = 0;                // sguardo nella posa ferma (MODE_HOLD)
uint8_t blinkPhase = 0, blinksPending = 0, blinkMask = LID_BOTH;   // fase: 0 nessuna, 1 chiusura, 2 chiuse, 3 apertura
uint8_t lastWink = LID_R;
uint32_t blinkHoldUntil = 0, nextGazeAt = 0, nextMicroAt = 0, nextBlinkAt = 0, nextMoodAt = 0;
uint32_t lastUpdate = 0, lastPcaTry = 0;
bool pcaOk = false;

void pickMood(uint32_t now) {
  uint16_t total = 0;
  for (uint8_t i = 0; i < N_MOODS; i++) total += MOODS[i].weight;
  long r = random(0, total);
  for (uint8_t i = 0; i < N_MOODS; i++) {
    if (r < MOODS[i].weight) { mood = i; break; }
    r -= MOODS[i].weight;
  }
  nextMoodAt = now + random(MOOD_MIN_MS, MOOD_MAX_MS);
  Serial.print(F("umore: ")); Serial.println(MOODS[mood].name);
}

// Apertura delle palpebre a riposo: dipende dall'umore e dallo sguardo su/giu'
float lidRest() {
  float y = gazeY.cur + microY;
  float follow = y < 0 ? LID_LOOK_DOWN * y : LID_LOOK_UP * y;
  return clampf(LID_OPEN_REST + MOODS[mood].lid + follow, LID_REST_MIN, 1.0f);
}

uint16_t fixationMs() {
  return (uint16_t)clampf(frand(FIX_MIN_MS, FIX_MAX_MS) * MOODS[mood].fix, 150, 12000);
}

void scheduleBlink(uint32_t now) {
  nextBlinkAt = now + (uint32_t)(frand(BLINK_MIN_MS, BLINK_MAX_MS) * MOODS[mood].blink);
}

void startBlink(uint32_t now, bool allowDouble, uint8_t mask) {
  if (blinkPhase) return;
  blinkMask = mask;
  blinksPending = (allowDouble && mask == LID_BOTH && chance(DOUBLE_BLINK_PROB)) ? 1 : 0;
  blinkPhase = 1;
  lid.cur = lidLevel;
  lid.go(0.0f, (uint16_t)(BLINK_CLOSE_MS / SPEED_SCALE), false, now);
}

void updateBlink(uint32_t now) {
  switch (blinkPhase) {
    case 1:
      if (lid.done(now)) {
        uint16_t hold = blinkMask == LID_BOTH ? BLINK_HOLD_MS : WINK_HOLD_MS;
        if (mood == MOOD_SLEEPY) hold = (uint16_t)(hold * frand(3.0f, 12.0f));   // palpebre "pesanti"
        blinkHoldUntil = now + hold;
        blinkPhase = 2;
      }
      break;
    case 2:
      if ((int32_t)(now - blinkHoldUntil) >= 0) {
        lid.go(lidLevel, (uint16_t)(BLINK_OPEN_MS / (MOODS[mood].speed * SPEED_SCALE)), true, now);
        blinkPhase = 3;
      }
      break;
    case 3:
      lid.to = lidLevel;                     // riapre fin dove intanto e' arrivato lo sguardo
      if (lid.done(now)) {
        if (blinksPending) { blinksPending--; blinkPhase = 0; startBlink(now, false, LID_BOTH); }
        else { blinkPhase = 0; scheduleBlink(now); }
      }
      break;
  }
  lid.update(now);
}

void pickGaze(uint32_t now) {
  const Mood &M = MOODS[mood];
  float rx = RANGE_X * M.range, ry = RANGE_Y * M.range, tx, ty;
  if (chance(0.05f)) { tx = frand(-0.1f, 0.1f); ty = frand(-0.1f, 0.1f); }        // torna a guardare davanti
  else if (chance(EXTREME_PROB)) {                                                 // verso un bordo o un angolo
    tx = (chance(0.5f) ? rx : -rx) * frand(0.75f, 1.0f);
    ty = chance(0.5f) ? (chance(0.5f) ? ry : -ry) * frand(0.6f, 1.0f) : frand(-ry, ry);
  }
  else if (chance(NEW_POINT_PROB)) { tx = frand(-rx, rx); ty = frand(-ry, ry); }   // punto nuovo
  else { tx = fixX + frand(-0.3f, 0.3f); ty = fixY + frand(-0.25f, 0.25f); }      // piccolo spostamento vicino
  tx = clampf(tx, -RANGE_X, RANGE_X);
  ty = clampf(ty, -RANGE_Y, RANGE_Y);

  gazeX.cur += microX; gazeY.cur += microY;  // la saccade parte da dove l'occhio e' davvero
  microX = microY = 0;
  float dist = hypotf(tx - gazeX.cur, ty - gazeY.cur);
  float sp = M.speed * SPEED_SCALE;
  uint16_t dur = (uint16_t)((SACCADE_BASE_MS + SACCADE_PER_UNIT * dist) / sp);
  bool glance = chance(GLANCE_PROB);
  if (glance) dur = (uint16_t)(dur * frand(3.0f, 6.0f));
  gazeX.go(tx, dur, glance, now);
  gazeY.go(ty, dur, glance, now);
  fixX = tx; fixY = ty;
  nextGazeAt = now + dur + fixationMs();
  nextMicroAt = now + dur + random(150, 500);
  if (dist > 0.6f && !glance && chance(BLINK_AFTER_BIG)) startBlink(now, true, LID_BOTH);
}

void writeServos(float x, float y, float lidL, float lidR) {
  outX.write(axisDeg(CAL_X, x));
  outY.write(axisDeg(CAL_Y, y));
  outLidL.write(lidDeg(CAL_LID_L, lidL));
  outLidR.write(lidDeg(CAL_LID_R, lidR));
}

void update(uint32_t now) {
  if (mode == MODE_HOLD) { writeServos(holdX, holdY, 1.0f, 1.0f); return; }
  if ((int32_t)(now - nextMoodAt) >= 0) pickMood(now);

  if (gazeX.done(now) && (int32_t)(now - nextGazeAt) >= 0) pickGaze(now);
  gazeX.update(now);
  gazeY.update(now);
  if (MICRO_AMP > 0 && gazeX.done(now) && (int32_t)(now - nextMicroAt) >= 0) {   // micro-movimenti
    microX = frand(-MICRO_AMP, MICRO_AMP);
    microY = frand(-MICRO_AMP, MICRO_AMP) * 0.7f;
    nextMicroAt = now + random(200, 700);
  }

  if (!blinkPhase && (int32_t)(now - nextBlinkAt) >= 0) {
    uint8_t mask = LID_BOTH;
    if (chance(WINK_PROB)) mask = chance(0.5f) ? LID_L : LID_R;
    startBlink(now, true, mask);
  }
  lidLevel += (lidRest() - lidLevel) * 0.1f;
  updateBlink(now);

  float lidL = (blinkPhase && (blinkMask & LID_L)) ? lid.cur : lidLevel;
  float lidR = (blinkPhase && (blinkMask & LID_R)) ? lid.cur : lidLevel;
  writeServos(gazeX.cur + microX, gazeY.cur + microY, lidL, lidR);
}

// Posizione iniziale, un servo alla volta (meno spunto sull'alimentazione)
void startServos() {
  float lv = lidRest();
  outX.write(axisDeg(CAL_X, 0));        delay(ATTACH_STEP_MS);
  outY.write(axisDeg(CAL_Y, 0));        delay(ATTACH_STEP_MS);
  outLidL.write(lidDeg(CAL_LID_L, lv)); delay(ATTACH_STEP_MS);
  outLidR.write(lidDeg(CAL_LID_R, lv)); delay(ATTACH_STEP_MS);
  uint32_t now = millis();
  nextGazeAt = now + random(300, 1500);
  scheduleBlink(now);
}

void updateLed(uint32_t now) {
  bool on;
  if (!pcaOk) on = (now % 200) < 100;                       // PCA9685 non trovata
  else if (mode != MODE_RANDOM) on = true;
  else on = (now % 3000) < 80;                              // un lampo ogni 3 s
#if defined(ESP8266)
  digitalWrite(LED_BUILTIN, !on);                           // LED del modulo: acceso a LOW
#else
  digitalWrite(LED_BUILTIN, on);
#endif
}

void printStatus() {
  Serial.print(F("EyeD85_random  PCA9685 0x")); Serial.print(PCA_ADDR, HEX);
  Serial.print(pcaOk ? F(" ok") : F(" NON TROVATA"));
  Serial.print(F("  modo=")); Serial.print(mode == MODE_RANDOM ? F("casuale") : F("fermo"));
  Serial.print(F("  umore=")); Serial.println(MOODS[mood].name);
  const Out *const OUTS[] = { &outX, &outY, &outLidL, &outLidR };
  static const char *const NAMES[] = { "X", "Y", "palpebre sx", "palpebre dx" };
  for (uint8_t i = 0; i < 4; i++) {
    Serial.print(i ? F("  ") : F("gradi: ")); Serial.print(NAMES[i]);
    Serial.print(F(" (canale ")); Serial.print(OUTS[i]->ch); Serial.print(F(")="));
    Serial.print(OUTS[i]->deg, 1);
  }
  Serial.println();
}

void handleSerial(uint32_t now) {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r' || c == ' ') continue;
    if (c == 'c' || (c >= '1' && c <= '9')) {   // posa ferma, tastierino numerico (c = 5)
      uint8_t k = c == 'c' ? 4 : c - '1';
      holdX = (float)(k % 3) - 1.0f;
      holdY = (float)(k / 3) - 1.0f;
      mode = MODE_HOLD;
      static const char *const POSE[] = { "in basso a sinistra", "in basso", "in basso a destra",
                                          "a sinistra", "al centro", "a destra",
                                          "in alto a sinistra", "in alto", "in alto a destra" };
      Serial.print(F("FERMO ")); Serial.print(POSE[k]);
      Serial.print(F(" (di chi guarda): X=")); Serial.print(axisDeg(CAL_X, holdX), 1);
      Serial.print(F(" Y=")); Serial.print(axisDeg(CAL_Y, holdY), 1);
      Serial.println(F(" gradi, palpebre aperte; 'r' per ripartire"));
    } else if (c == 'r') {
      mode = MODE_RANDOM;
      nextGazeAt = now;
      Serial.println(F("movimento casuale"));
    } else if (c == 'b') {
      startBlink(now, false, LID_BOTH);
    } else if (c == 'w') {
      lastWink = lastWink == LID_L ? LID_R : LID_L;
      startBlink(now, false, lastWink);
    } else if (c == 's') {
      printStatus();
    } else {
      Serial.println(F("comandi: c r b w s, 1-9 posa ferma (4/6 sx/dx, 8/2 su/giu', 5 centro)"));
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
#if defined(ESP8266)
  WiFi.mode(WIFI_OFF);                       // niente WiFi: meno consumo e niente riconnessioni
  randomSeed(ESP.random());                  // generatore hardware: ogni accensione e' diversa
#else
  randomSeed(analogRead(A0) ^ micros());
#endif
  delay(200);
  Serial.println();
  outX.ch = CH_X;
  outY.ch = CH_Y;
  outLidL.ch = CH_LID_L;
  outLidR.ch = CH_LID_R;
  pcaOk = pcaBegin();
  if (pcaOk) startServos();
  else Serial.println(F("ERRORE: PCA9685 non risponde (cavi SDA/SCL, VCC 3.3 V, GND comune, indirizzo)"));
  pickMood(millis());
  printStatus();
  lastUpdate = lastPcaTry = millis();
}

void loop() {
  uint32_t now = millis();
  handleSerial(now);
  if (now - lastUpdate < UPDATE_MS) return;
  lastUpdate = now;
  updateLed(now);
  if (!pcaOk) {                              // riprova ogni 2 s (es. PCA9685 collegata dopo)
    if (now - lastPcaTry > 2000) {
      lastPcaTry = now;
      pcaOk = pcaBegin();
      if (pcaOk) { Serial.println(F("PCA9685 trovata")); startServos(); }
    }
    return;
  }
  update(now);
}

