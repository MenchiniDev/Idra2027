// =====================================================================
//  EyeNode_random — movimento autonomo e casuale degli occhi di una testa
//  L'Idra, Carnevale di Viareggio 2027 — scheda EyeNode (Arduino Nano)
// =====================================================================
//  Ogni testa e' indipendente: nessun bus, nessun master. Il carattere
//  della testa (velocita', ampiezza, frequenza dei battiti, direzione
//  preferita) viene estratto a caso all'accensione da un seme che
//  dipende dall'indirizzo DIP, da un contatore di accensioni in EEPROM
//  e dal rumore degli ingressi analogici: due teste non si muovono mai
//  allo stesso modo, e la stessa testa cambia a ogni accensione.
//
//  Comportamento:
//    - fissazione di un punto (tempo casuale) con micro-movimenti
//    - saccade (spostamento rapido) verso un nuovo punto, a volte lento
//    - battiti di ciglia casuali, a volte doppi, spesso dopo un grande
//      spostamento; le palpebre seguono lo sguardo su/giu'
//    - "umore" che cambia ogni 1–4 minuti: calmo, curioso, agitato,
//      assonnato
//
//  Seriale 115200: 'c' = tutti i servo al centro e palpebre aperte
//  (per montare le squadrette), 'r' = riprende il movimento casuale,
//  'b' = battito di ciglia, 's' = stato.
//
//  Librerie: solo Servo ed EEPROM (incluse nell'IDE Arduino).
// =====================================================================
#include <Servo.h>
#include <EEPROM.h>
#include <math.h>
#include "config.h"

// ----------------------------------------------------------- pin scheda
const uint8_t PIN_SERVO[2][3] = { {3, 5, 6}, {9, 10, 11} };   // [occhio][sx/dx, su/giu, palpebre]
const uint8_t PIN_ADDR[4] = { A0, A1, A2, A3 };
const uint8_t PIN_LED = 12;
const uint8_t PIN_VSENSE = A7;
const uint8_t PIN_AUX_A6 = A6;
const uint16_t UPDATE_MS = 10;
const int EEPROM_BOOT_ADDR = 0;

enum Axis { LR = 0, UD = 1, LID = 2 };
enum Mode { MODE_RANDOM, MODE_CENTER, MODE_PARKED };

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

// ----------------------------------------------------------- carattere e umore
struct Personality {
  float speed, fixScale, blinkScale, rangeLR, rangeUD, biasLR, biasUD, curiosity, vergence, lidOpen;
};

struct Mood { const char *name; float fix, speed, range, blink, lid; uint8_t weight; };
const Mood MOODS[] = {
  // nome        fissaz. veloc. ampiezza battiti palpebre peso
  { "calmo",     1.6f,   0.80f, 0.60f,   1.30f,  0.00f,   30 },
  { "curioso",   1.0f,   1.00f, 1.00f,   1.00f,  0.05f,   40 },
  { "agitato",   0.45f,  1.25f, 1.00f,   0.60f,  0.08f,   20 },
  { "assonnato", 2.0f,   0.60f, 0.50f,   1.80f, -0.35f,   10 },
};
const uint8_t MOOD_CALM = 0, MOOD_SLEEPY = 3, N_MOODS = sizeof(MOODS) / sizeof(MOODS[0]);

// ----------------------------------------------------------- stato
Servo servo[2][3];
uint8_t addr = 0, nEyes = 2;
uint32_t seed = 0;
uint16_t bootCount = 0;
Personality P;
uint8_t mood = 1;
Mode mode = MODE_RANDOM;

Move gazeLR, gazeUD, lid;
float fixLR = 0, fixUD = 0;          // punto fissato (i micro-movimenti ci girano attorno)
float lidLevel = 0.9f;               // palpebre a riposo (filtrate)
uint8_t blinkPhase = 0;              // 0 nessuno, 1 chiusura, 2 chiuse, 3 apertura
uint8_t blinksPending = 0;
uint32_t blinkHoldUntil = 0;
uint32_t nextGazeAt = 0, nextBlinkAt = 0, nextMicroAt = 0, nextMoodAt = 0;
uint32_t lastUpdate = 0;

float vservo = 6.0f, vbatt = 12.8f;
uint32_t lowServoSince = 0, critBattSince = 0;
bool servoLow = false, battLow = false;

// ----------------------------------------------------------- ingressi
uint8_t readAddress() {
  uint8_t a = 0;
  for (uint8_t i = 0; i < 4; i++) {
    pinMode(PIN_ADDR[i], INPUT_PULLUP);
  }
  delay(5);
  for (uint8_t i = 0; i < 4; i++) {
    if (digitalRead(PIN_ADDR[i]) == LOW) a |= (1 << i);   // DIP ON = chiuso a GND = bit 1
  }
  return a;
}

uint32_t makeSeed(uint8_t a) {
  EEPROM.get(EEPROM_BOOT_ADDR, bootCount);
  bootCount++;
  EEPROM.put(EEPROM_BOOT_ADDR, bootCount);
  uint32_t h = 2166136261UL;                               // FNV-1a
  auto mix = [&](uint32_t v) { for (uint8_t i = 0; i < 4; i++) { h ^= (v >> (8 * i)) & 0xFF; h *= 16777619UL; } };
  mix(a);
  mix(bootCount);
  for (uint8_t i = 0; i < 48; i++) {                       // rumore ADC + jitter temporale
    mix(analogRead(PIN_AUX_A6) ^ ((uint32_t)analogRead(PIN_VSENSE) << 10) ^ micros());
    delayMicroseconds(13 + (h & 63));
  }
  return h ? h : 0x1DA2027UL;
}

// ----------------------------------------------------------- carattere / umore
void rollPersonality() {
  P.speed      = frand(0.80f, 1.25f);
  P.fixScale   = frand(0.70f, 1.50f);
  P.blinkScale = frand(0.70f, 1.40f);
  P.rangeLR    = frand(RANGE_LR_MIN, RANGE_LR_MAX);
  P.rangeUD    = frand(RANGE_UD_MIN, RANGE_UD_MAX);
  P.biasLR     = frand(-BIAS_LR_MAX, BIAS_LR_MAX);
  P.biasUD     = frand(-BIAS_UD_MAX, BIAS_UD_MAX);
  P.curiosity  = frand(0.25f, 0.60f);
  P.vergence   = nEyes == 2 ? frand(0.0f, 0.06f) : 0.0f;
  P.lidOpen    = frand(0.75f, 0.95f);
  // direzione preferita + ampiezza non devono superare la corsa calibrata
  P.rangeLR = min(P.rangeLR, 0.95f - fabs(P.biasLR));
  P.rangeUD = min(P.rangeUD, 0.95f - fabs(P.biasUD));
}

void pickMood(uint32_t now) {
  uint16_t total = 0;
  for (uint8_t i = 0; i < N_MOODS; i++) total += MOODS[i].weight;
  long r = random(0, total);
  for (uint8_t i = 0; i < N_MOODS; i++) {
    if (r < MOODS[i].weight) { mood = i; break; }
    r -= MOODS[i].weight;
  }
  if (battLow) mood = MOOD_SLEEPY;
  else if (servoLow) mood = MOOD_CALM;
  nextMoodAt = now + random(MOOD_MIN_MS, MOOD_MAX_MS);
  Serial.print(F("umore: ")); Serial.println(MOODS[mood].name);
}

// ----------------------------------------------------------- comportamento
float lidRest() {
  const Mood &M = MOODS[mood];
  return clampf(P.lidOpen + M.lid + LID_FOLLOW * gazeUD.cur, LID_REST_MIN, 1.0f);
}

uint16_t fixationMs() {
  const Mood &M = MOODS[mood];
  return (uint16_t)clampf(frand(FIX_MIN_MS, FIX_MAX_MS) * P.fixScale * M.fix, 120, 12000);
}

void startBlink(uint32_t now, bool allowDouble) {
  if (blinkPhase) return;
  blinksPending = (allowDouble && chance(DOUBLE_BLINK_PROB)) ? 1 : 0;
  blinkPhase = 1;
  lid.cur = lidLevel;
  lid.go(0.0f, BLINK_CLOSE_MS, false, now);
}

void scheduleBlink(uint32_t now) {
  const Mood &M = MOODS[mood];
  nextBlinkAt = now + (uint32_t)(frand(BLINK_MIN_MS, BLINK_MAX_MS) * P.blinkScale * M.blink);
}

void updateBlink(uint32_t now) {
  lid.update(now);
  switch (blinkPhase) {
    case 1:
      if (lid.done(now)) {
        uint16_t hold = BLINK_HOLD_MS;
        if (mood == MOOD_SLEEPY) hold = (uint16_t)(hold * frand(3.0f, 12.0f));   // palpebre "pesanti"
        blinkHoldUntil = now + hold;
        blinkPhase = 2;
      }
      break;
    case 2:
      if ((int32_t)(now - blinkHoldUntil) >= 0) {
        lid.go(lidRest(), (uint16_t)(BLINK_OPEN_MS / MOODS[mood].speed), true, now);
        blinkPhase = 3;
      }
      break;
    case 3:
      if (lid.done(now)) {
        lidLevel = lid.cur;
        if (blinksPending) { blinksPending--; blinkPhase = 0; startBlink(now, false); }
        else { blinkPhase = 0; scheduleBlink(now); }
      }
      break;
  }
}

void pickGaze(uint32_t now) {
  const Mood &M = MOODS[mood];
  float rLR = P.rangeLR * M.range, rUD = P.rangeUD * M.range;
  float tLR, tUD;
  bool big;
  if (chance(0.08f)) {                         // torna a guardare "davanti"
    tLR = P.biasLR + frand(-0.1f, 0.1f);
    tUD = P.biasUD + frand(-0.1f, 0.1f);
  } else if (chance(P.curiosity)) {            // nuovo punto ovunque nel suo range
    tLR = P.biasLR + frand(-rLR, rLR);
    tUD = P.biasUD + frand(-rUD, rUD);
  } else {                                     // piccolo spostamento vicino
    tLR = fixLR + frand(-0.18f, 0.18f);
    tUD = fixUD + frand(-0.12f, 0.12f);
  }
  tLR = clampf(tLR, P.biasLR - P.rangeLR, P.biasLR + P.rangeLR);   // mai oltre il range della testa
  tUD = clampf(tUD, P.biasUD - P.rangeUD, P.biasUD + P.rangeUD);

  float dist = max(fabs(tLR - gazeLR.cur), fabs(tUD - gazeUD.cur));
  big = dist > 0.5f;
  float speed = P.speed * M.speed * SPEED_SCALE;
  uint16_t dur = (uint16_t)((SACCADE_BASE_MS + SACCADE_PER_UNIT * dist) / speed);
  bool glance = chance(GLANCE_PROB);
  if (glance) dur = (uint16_t)(dur * frand(3.0f, 6.0f));

  gazeLR.go(tLR, dur, glance, now);
  gazeUD.go(tUD, dur, glance, now);
  fixLR = tLR; fixUD = tUD;
  nextGazeAt = now + dur + fixationMs();
  nextMicroAt = now + dur + random(150, 600);

  if (big && !glance && chance(BLINK_AFTER_BIG)) startBlink(now, true);
}

void microMove(uint32_t now) {
  if (MICRO_AMP <= 0) return;
  gazeLR.go(clampf(fixLR + frand(-MICRO_AMP, MICRO_AMP), -1, 1), 45, false, now);
  gazeUD.go(clampf(fixUD + frand(-MICRO_AMP, MICRO_AMP), -1, 1), 45, false, now);
  nextMicroAt = now + random(250, 900);
}

// ----------------------------------------------------------- uscite servo
int toUs(const ServoCal &c, float v) {
  v = clampf(v, -1.0f, 1.0f);
  return v >= 0 ? c.mid + (int)((c.pos - c.mid) * v) : c.mid + (int)((c.mid - c.neg) * v);
}
int lidUs(const LidCal &c, float v) {
  return c.closed + (int)((c.open - c.closed) * clampf(v, 0.0f, 1.0f));
}

void writeEyes(float lr, float ud, float lv) {
  uint8_t ci = addr <= MAX_ADDR ? addr : 0;
  for (uint8_t e = 0; e < nEyes; e++) {
    const EyeCal &cal = CAL[ci][e];
    float v = (e == 0) ? P.vergence : -P.vergence;   // occhi leggermente convergenti
    servo[e][LR].writeMicroseconds(toUs(cal.lr, lr + v));
    servo[e][UD].writeMicroseconds(toUs(cal.ud, ud));
    servo[e][LID].writeMicroseconds(lidUs(cal.lid, lv));
  }
}

void attachAll() {
  for (uint8_t e = 0; e < nEyes; e++)
    for (uint8_t a = 0; a < 3; a++) {
      if (servo[e][a].attached()) continue;
      servo[e][a].attach(PIN_SERVO[e][a], 500, 2500);
      delay(ATTACH_STEP_MS);                            // uno alla volta: meno spunto
    }
}

void detachAll() {
  for (uint8_t e = 0; e < nEyes; e++)
    for (uint8_t a = 0; a < 3; a++) servo[e][a].detach();
}

// ----------------------------------------------------------- tensioni
void readVoltages(uint32_t now) {
  float vs = analogRead(PIN_VSENSE) * (5.0f / 1023.0f) * 2.0f;
  vservo += (vs - vservo) * 0.05f;
  if (vservo < VSERVO_LOW) {
    if (!lowServoSince) lowServoSince = now;
    if (!servoLow && now - lowServoSince > 3000) {
      servoLow = true; mood = MOOD_CALM;
      Serial.println(F("ATTENZIONE: VSERVO bassa, movimento ridotto"));
    }
  } else { lowServoSince = 0; servoLow = false; }

#if BATT_SENSE_ENABLED
  float vb = analogRead(PIN_AUX_A6) * (5.0f / 1023.0f) * BATT_DIVIDER;
  vbatt += (vb - vbatt) * 0.02f;
  battLow = vbatt < BATT_LOW;
  if (battLow && mood != MOOD_SLEEPY && mode == MODE_RANDOM) mood = MOOD_SLEEPY;
  if (mode == MODE_RANDOM && vbatt < BATT_CRIT) {
    if (!critBattSince) critBattSince = now;
    if (now - critBattSince > 10000UL) {               // la testa "si addormenta"
      Serial.println(F("BATTERIA SCARICA: occhi chiusi, servo staccati"));
      writeEyes(0, -0.3f, 0.0f);
      delay(600);
      detachAll();
      mode = MODE_PARKED;
    }
  } else critBattSince = 0;
  if (mode == MODE_PARKED && vbatt > BATT_RESUME) {
    Serial.println(F("batteria ok, riparto"));
    attachAll();
    mode = MODE_RANDOM;
  }
#endif
}

// ----------------------------------------------------------- LED di stato
void updateLed(uint32_t now) {
  bool on;
  if (mode == MODE_CENTER) on = true;
  else if (mode == MODE_PARKED) on = (now % 4000) < 150;
  else if (servoLow || battLow) on = (now % 250) < 60;
  else {                                   // ogni 3 s lampeggia 'addr' volte (identifica la testa)
    uint16_t t = now % 3000;
    uint8_t n = addr ? addr : 1;
    on = t < n * 300u && (t % 300) < 120;
  }
  digitalWrite(PIN_LED, on);
}

// ----------------------------------------------------------- seriale
void printStatus() {
  Serial.print(F("EyeNode addr=")); Serial.print(addr);
  Serial.print(F(" occhi=")); Serial.print(nEyes);
  Serial.print(F(" boot=")); Serial.print(bootCount);
  Serial.print(F(" seed=0x")); Serial.println(seed, HEX);
  Serial.print(F(" carattere: veloc=")); Serial.print(P.speed, 2);
  Serial.print(F(" fissaz=")); Serial.print(P.fixScale, 2);
  Serial.print(F(" battiti=")); Serial.print(P.blinkScale, 2);
  Serial.print(F(" range=")); Serial.print(P.rangeLR, 2); Serial.print('/'); Serial.print(P.rangeUD, 2);
  Serial.print(F(" bias=")); Serial.print(P.biasLR, 2); Serial.print('/'); Serial.print(P.biasUD, 2);
  Serial.print(F(" curiosita=")); Serial.println(P.curiosity, 2);
  Serial.print(F(" umore=")); Serial.print(MOODS[mood].name);
  Serial.print(F(" VSERVO=")); Serial.print(vservo, 2);
#if BATT_SENSE_ENABLED
  Serial.print(F(" VBATT=")); Serial.print(vbatt, 2);
#endif
  Serial.println();
}

void handleSerial(uint32_t now) {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'c') { mode = MODE_CENTER; Serial.println(F("CENTRO: sx/dx=0 su/giu=0 palpebre aperte")); }
    else if (c == 'r') {
      if (mode == MODE_PARKED) attachAll();
      mode = MODE_RANDOM; nextGazeAt = now; Serial.println(F("movimento casuale"));
    }
    else if (c == 'b') startBlink(now, false);
    else if (c == 's') printStatus();
  }
}

// ----------------------------------------------------------- setup / loop
void setup() {
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
  addr = readAddress();
  nEyes = EYES_FOR_ADDR[addr <= MAX_ADDR ? addr : 0];
  seed = makeSeed(addr);
  randomSeed(seed);
  rollPersonality();

  // posizione iniziale scritta PRIMA di agganciare: il primo impulso e' gia' giusto
  gazeLR.cur = P.biasLR; gazeUD.cur = P.biasUD; lidLevel = P.lidOpen;
  writeEyes(gazeLR.cur, gazeUD.cur, lidLevel);
  delay(addr * START_DELAY_PER_ADDR_MS + random(0, 400));   // le teste partono sfasate
  attachAll();

  uint32_t now = millis();
  pickMood(now);
  printStatus();
  nextGazeAt = now + random(300, 2000);
  scheduleBlink(now);
  lastUpdate = now;
}

void loop() {
  uint32_t now = millis();
  handleSerial(now);
  if (now - lastUpdate < UPDATE_MS) return;
  lastUpdate = now;

  readVoltages(now);
  updateLed(now);

  if (mode == MODE_PARKED) return;
  if (mode == MODE_CENTER) { writeEyes(0, 0, 1.0f); return; }

  if ((int32_t)(now - nextMoodAt) >= 0) pickMood(now);

  bool moving = !gazeLR.done(now) || !gazeUD.done(now);
  if (!moving && (int32_t)(now - nextGazeAt) >= 0) pickGaze(now);
  else if (!moving && (int32_t)(now - nextMicroAt) >= 0 && nextGazeAt - now > 150) microMove(now);
  gazeLR.update(now);
  gazeUD.update(now);

  if (!blinkPhase && (int32_t)(now - nextBlinkAt) >= 0) startBlink(now, true);
  updateBlink(now);
  if (!blinkPhase) lidLevel += (lidRest() - lidLevel) * 0.08f;   // palpebre seguono lo sguardo

  writeEyes(gazeLR.cur, gazeUD.cur, blinkPhase ? lid.cur : lidLevel);
}
