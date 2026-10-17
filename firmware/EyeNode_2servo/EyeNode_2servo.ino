// =====================================================================
//  EyeNode_2servo — occhi a 2 servo (sx/dx + palpebre) per L'Idra 2027
// =====================================================================
//  Ogni testa ha una coppia di occhi mossa da 2 MG995: uno gira i due
//  bulbi insieme (sx/dx), l'altro muove le palpebre dei due occhi.
//
//  Due architetture, scelte in config.h (CENTRAL_PCA9685):
//    0 = un Arduino Nano per testa (scheda EyeNode): questo sketch muove
//        UNA testa; l'indirizzo arriva dal DIP switch.
//    1 = un solo Arduino Nano alla base: muove TUTTE le teste tramite una
//        PCA9685 (I2C). Ogni testa resta indipendente: carattere, umore e
//        tempi propri, nessuna sincronia.
//
//  Comportamento di ogni testa (come EyeNode_random, senza su/giu'):
//    fissazione di un punto -> saccade verso un nuovo punto (a volte uno
//    spostamento lento di scansione); battiti di ciglia casuali, a volte
//    doppi, spesso dopo un grande spostamento; "umore" che cambia ogni
//    1-4 minuti (calmo, curioso, agitato, assonnato).
//
//  Seriale 115200, comandi terminati da Invio:
//    c        tutti i servo al centro, palpebre aperte (montaggio squadrette)
//    r        riprende il movimento casuale
//    b        battito di ciglia (testa selezionata)
//    s        stato
//    h<n>     seleziona la testa n (solo architettura 1)
//    l<us>    servo sx/dx della testa selezionata a <us> microsecondi (es. l1500)
//    p<us>    servo palpebre della testa selezionata a <us> microsecondi
//  l/p mettono la testa in modo manuale: servono a trovare i valori da
//  scrivere in config.h. 'r' per tornare al movimento casuale.
//
//  Librerie: Servo (architettura 0) o Wire (architettura 1), EEPROM.
// =====================================================================
#include <EEPROM.h>
#include <math.h>
#include "config.h"

#if CENTRAL_PCA9685
  #include <Wire.h>
  const uint8_t N_HEADS = N_HEADS_CENTRAL;
#else
  #include <Servo.h>
  const uint8_t N_HEADS = 1;
#endif

// ----------------------------------------------------------- pin scheda
const uint8_t PIN_ADDR[4] = { A0, A1, A2, A3 };
const uint8_t PIN_LED = 12;
const uint8_t PIN_VSENSE = A7;
const uint8_t PIN_NOISE = A6;
const uint16_t UPDATE_MS = 10;
const int EEPROM_BOOT_ADDR = 0;

enum Mode { MODE_RANDOM, MODE_CENTER, MODE_MANUAL };

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
  { "calmo",     1.6f,   0.80f, 0.60f,   1.30f,  0.00f,   30 },
  { "curioso",   1.0f,   1.00f, 1.00f,   1.00f,  0.05f,   40 },
  { "agitato",   0.45f,  1.25f, 1.00f,   0.60f,  0.08f,   20 },
  { "assonnato", 2.0f,   0.60f, 0.50f,   1.80f, -0.35f,   10 },
};
const uint8_t MOOD_CALM = 0, MOOD_SLEEPY = 3, N_MOODS = sizeof(MOODS) / sizeof(MOODS[0]);

// ----------------------------------------------------------- uscite servo
#if CENTRAL_PCA9685
// Driver minimo PCA9685 (senza librerie esterne)
float pcaHz = 50.0f;
void pcaWrite8(uint8_t reg, uint8_t v) {
  Wire.beginTransmission(PCA_ADDR); Wire.write(reg); Wire.write(v); Wire.endTransmission();
}
bool pcaBegin() {
  Wire.begin();
  Wire.setClock(100000);                     // 100 kHz: piu' robusto su cavi lunghi
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
#endif

struct Out {                       // un'uscita servo (pin del Nano o canale PCA9685)
  uint8_t pin = 0;
  bool attached = false;
  int lastUs = -1;
#if !CENTRAL_PCA9685
  Servo s;
#endif
  void write(int us) {
    if (us == lastUs && attached) return;
    lastUs = us;
#if CENTRAL_PCA9685
    uint16_t ticks = (uint16_t)(us * 4096.0f * pcaHz / 1000000.0f + 0.5f);
    pcaChannel(pin, 0, ticks);
    attached = true;
#else
    s.writeMicroseconds(us);       // scritto prima dell'attach: il primo impulso e' gia' giusto
#endif
  }
  void attach() {
    if (attached) return;
#if CENTRAL_PCA9685
    attached = true;
    int us = lastUs; lastUs = -1; if (us > 0) write(us);
#else
    s.attach(pin, 500, 2500);
    attached = true;
#endif
  }
  void detach() {
    if (!attached) return;
#if CENTRAL_PCA9685
    pcaChannel(pin, 0, 0x1000);    // FULL_OFF: nessun impulso
#else
    s.detach();
#endif
    attached = false;
  }
};

// ----------------------------------------------------------- testa
struct Head {
  uint8_t id = 0;                  // indice in CAL
  Out lrOut, lidOut;
  // carattere
  float speed, fixScale, blinkScale, rangeLR, biasLR, curiosity, lidOpen;
  uint8_t mood = 1;
  Mode mode = MODE_RANDOM;
  Move gaze, lid;
  float fix = 0, lidLevel = 0.9f;
  uint8_t blinkPhase = 0, blinksPending = 0;   // 0 nessuno, 1 chiusura, 2 chiuse, 3 apertura
  uint32_t blinkHoldUntil = 0, nextGazeAt = 0, nextBlinkAt = 0, nextMoodAt = 0, stillSince = 0;
  int manualLr = 1500, manualLid = 1500;

  const HeadCal &cal() const { return CAL[id <= MAX_HEAD ? id : 0]; }

  void rollPersonality() {
    speed      = frand(0.80f, 1.25f);
    fixScale   = frand(0.70f, 1.50f);
    blinkScale = frand(0.70f, 1.40f);
    rangeLR    = frand(RANGE_LR_MIN, RANGE_LR_MAX);
    biasLR     = frand(-BIAS_LR_MAX, BIAS_LR_MAX);
    curiosity  = frand(0.25f, 0.60f);
    lidOpen    = frand(0.75f, 0.95f);
    rangeLR    = min(rangeLR, 0.95f - (float)fabs(biasLR));   // mai oltre la corsa calibrata
  }

  void pickMood(uint32_t now, bool forceCalm, bool forceSleepy) {
    uint16_t total = 0;
    for (uint8_t i = 0; i < N_MOODS; i++) total += MOODS[i].weight;
    long r = random(0, total);
    for (uint8_t i = 0; i < N_MOODS; i++) {
      if (r < MOODS[i].weight) { mood = i; break; }
      r -= MOODS[i].weight;
    }
    if (forceSleepy) mood = MOOD_SLEEPY;
    else if (forceCalm) mood = MOOD_CALM;
    nextMoodAt = now + random(MOOD_MIN_MS, MOOD_MAX_MS);
    Serial.print(F("testa ")); Serial.print(id); Serial.print(F(" umore: ")); Serial.println(MOODS[mood].name);
  }

  float lidRest() const { return clampf(lidOpen + MOODS[mood].lid, LID_REST_MIN, 1.0f); }

  uint16_t fixationMs() const {
    return (uint16_t)clampf(frand(FIX_MIN_MS, FIX_MAX_MS) * fixScale * MOODS[mood].fix, 150, 12000);
  }

  void scheduleBlink(uint32_t now) {
    nextBlinkAt = now + (uint32_t)(frand(BLINK_MIN_MS, BLINK_MAX_MS) * blinkScale * MOODS[mood].blink);
  }

  void startBlink(uint32_t now, bool allowDouble) {
    if (blinkPhase) return;
    blinksPending = (allowDouble && chance(DOUBLE_BLINK_PROB)) ? 1 : 0;
    blinkPhase = 1;
    lid.cur = lidLevel;
    lid.go(0.0f, (uint16_t)(BLINK_CLOSE_MS / SPEED_SCALE), false, now);
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
          lid.go(lidRest(), (uint16_t)(BLINK_OPEN_MS / (MOODS[mood].speed * SPEED_SCALE)), true, now);
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
    float r = rangeLR * M.range, t;
    if (chance(0.08f)) t = biasLR + frand(-0.1f, 0.1f);          // torna a guardare "davanti"
    else if (chance(curiosity)) t = biasLR + frand(-r, r);       // nuovo punto nel suo range
    else t = fix + frand(-0.2f, 0.2f);                           // piccolo spostamento vicino
    t = clampf(t, biasLR - rangeLR, biasLR + rangeLR);

    float dist = fabs(t - gaze.cur);
    float sp = speed * M.speed * SPEED_SCALE;
    uint16_t dur = (uint16_t)((SACCADE_BASE_MS + SACCADE_PER_UNIT * dist) / sp);
    bool glance = chance(GLANCE_PROB);
    if (glance) dur = (uint16_t)(dur * frand(3.0f, 6.0f));
    gaze.go(t, dur, glance, now);
    fix = t;
    nextGazeAt = now + dur + fixationMs();
    if (dist > 0.5f && !glance && chance(BLINK_AFTER_BIG)) startBlink(now, true);
  }

  static int toUs(const ServoCal &c, float v) {
    v = clampf(v, -1.0f, 1.0f);
    return v >= 0 ? c.mid + (int)((c.pos - c.mid) * v) : c.mid + (int)((c.mid - c.neg) * v);
  }
  static int lidUs(const LidCal &c, float v) {
    return c.closed + (int)((c.open - c.closed) * clampf(v, 0.0f, 1.0f));
  }

  void write(float lr, float lv) {
    lrOut.write(toUs(cal().lr, lr));
    lidOut.write(lidUs(cal().lid, lv));
  }

  void begin(uint32_t now) {
    rollPersonality();
    gaze.cur = biasLR; fix = biasLR; lidLevel = lidOpen;
    write(gaze.cur, lidLevel);
    nextGazeAt = now + random(300, 2000);
    scheduleBlink(now);
  }

  void update(uint32_t now, bool servoLow) {
    if (mode == MODE_CENTER) { lrOut.attach(); write(0, 1.0f); return; }
    if (mode == MODE_MANUAL) {
      lrOut.attach(); lidOut.attach();
      lrOut.write(manualLr); lidOut.write(manualLid);
      return;
    }
    if ((int32_t)(now - nextMoodAt) >= 0) pickMood(now, servoLow, false);

    bool moving = !gaze.done(now);
    if (!moving && (int32_t)(now - nextGazeAt) >= 0) { pickGaze(now); moving = true; }
    gaze.update(now);

    if (!blinkPhase && (int32_t)(now - nextBlinkAt) >= 0) startBlink(now, true);
    updateBlink(now);
    if (!blinkPhase) lidLevel += (lidRest() - lidLevel) * 0.05f;

    // riposo del servo sx/dx (evita il ronzio da fermo, se abilitato)
    if (moving) { stillSince = now; lrOut.attach(); }
    else if (HOLD_RELEASE_MS && now - stillSince > HOLD_RELEASE_MS) lrOut.detach();

    write(gaze.cur, blinkPhase ? lid.cur : lidLevel);
  }

  void printStatus() const {
    Serial.print(F("testa ")); Serial.print(id);
    Serial.print(F(": veloc=")); Serial.print(speed, 2);
    Serial.print(F(" fissaz=")); Serial.print(fixScale, 2);
    Serial.print(F(" battiti=")); Serial.print(blinkScale, 2);
    Serial.print(F(" range=")); Serial.print(rangeLR, 2);
    Serial.print(F(" bias=")); Serial.print(biasLR, 2);
    Serial.print(F(" umore=")); Serial.print(MOODS[mood].name);
    Serial.print(F(" us sx/dx=")); Serial.print(lrOut.lastUs);
    Serial.print(F(" palpebre=")); Serial.println(lidOut.lastUs);
  }
};

// ----------------------------------------------------------- stato globale
Head heads[N_HEADS];
uint8_t addr = 0, sel = 0;
uint32_t seed = 0, lastUpdate = 0, lowServoSince = 0;
uint16_t bootCount = 0;
float vservo = 6.0f;
bool servoLow = false, pcaOk = true;
char line[12];
uint8_t lineLen = 0;

uint8_t readAddress() {
  uint8_t a = 0;
  for (uint8_t i = 0; i < 4; i++) pinMode(PIN_ADDR[i], INPUT_PULLUP);
  delay(5);
  for (uint8_t i = 0; i < 4; i++) if (digitalRead(PIN_ADDR[i]) == LOW) a |= (1 << i);
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
    mix(analogRead(PIN_NOISE) ^ ((uint32_t)analogRead(PIN_VSENSE) << 10) ^ micros());
    delayMicroseconds(13 + (h & 63));
  }
  return h ? h : 0x1DA2027UL;
}

void readVoltage(uint32_t now) {
#if VSERVO_SENSE_ENABLED && !CENTRAL_PCA9685
  float vs = analogRead(PIN_VSENSE) * (5.0f / 1023.0f) * 2.0f;
  vservo += (vs - vservo) * 0.05f;
  if (vservo < VSERVO_LOW) {
    if (!lowServoSince) lowServoSince = now;
    if (!servoLow && now - lowServoSince > 3000) {
      servoLow = true;
      for (uint8_t i = 0; i < N_HEADS; i++) heads[i].mood = MOOD_CALM;
      Serial.println(F("ATTENZIONE: VSERVO bassa, movimento ridotto"));
    }
  } else { lowServoSince = 0; servoLow = false; }
#else
  (void)now;
#endif
}

void updateLed(uint32_t now) {
  bool on;
  if (!pcaOk) on = (now % 200) < 100;                       // PCA9685 non trovata
  else if (heads[0].mode != MODE_RANDOM) on = true;
  else if (servoLow) on = (now % 250) < 60;
  else {                                                    // ogni 3 s lampeggia N volte
    uint16_t t = now % 3000;
    uint8_t n = CENTRAL_PCA9685 ? N_HEADS : (addr ? addr : 1);
    on = t < n * 300u && (t % 300) < 120;
  }
  digitalWrite(PIN_LED, on);
}

void printStatus() {
  Serial.print(CENTRAL_PCA9685 ? F("EyeNode_2servo CENTRALE (PCA9685") : F("EyeNode_2servo testa (DIP addr="));
  Serial.print(CENTRAL_PCA9685 ? (pcaOk ? F(" ok") : F(" NON TROVATA")) : F(""));
  if (!CENTRAL_PCA9685) Serial.print(addr);
  Serial.print(F(") boot=")); Serial.print(bootCount);
  Serial.print(F(" seed=0x")); Serial.print(seed, HEX);
  Serial.print(F(" VSERVO=")); Serial.println(vservo, 2);
  for (uint8_t i = 0; i < N_HEADS; i++) heads[i].printStatus();
}

void command(uint32_t now) {
  char c = line[0];
  int v = atoi(line + 1);
  Head &H = heads[sel];
  if (c == 'c') {
    for (uint8_t i = 0; i < N_HEADS; i++) heads[i].mode = MODE_CENTER;
    Serial.println(F("CENTRO: sx/dx = mid, palpebre aperte"));
  } else if (c == 'r') {
    for (uint8_t i = 0; i < N_HEADS; i++) { heads[i].mode = MODE_RANDOM; heads[i].nextGazeAt = now; }
    Serial.println(F("movimento casuale"));
  } else if (c == 'b') {
    H.startBlink(now, false);
  } else if (c == 's') {
    printStatus();
  } else if (c == 'h' && CENTRAL_PCA9685) {
    if (v >= 0 && v < N_HEADS) sel = v;
    Serial.print(F("testa selezionata: ")); Serial.println(sel);
  } else if ((c == 'l' || c == 'p') && v >= 500 && v <= 2500) {
    if (H.mode != MODE_MANUAL) { H.manualLr = H.lrOut.lastUs; H.manualLid = H.lidOut.lastUs; H.mode = MODE_MANUAL; }
    if (c == 'l') H.manualLr = v; else H.manualLid = v;
    Serial.print(F("testa ")); Serial.print(H.id);
    Serial.print(F(" MANUALE sx/dx=")); Serial.print(H.manualLr);
    Serial.print(F(" palpebre=")); Serial.println(H.manualLid);
  } else {
    Serial.println(F("comandi: c r b s h<n> l<us> p<us>"));
  }
}

void handleSerial(uint32_t now) {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen) { line[lineLen] = 0; command(now); lineLen = 0; }
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = c;
      if (lineLen == 1 && (c == 'c' || c == 'r' || c == 'b' || c == 's')) {   // comandi di 1 lettera: subito
        line[1] = 0; command(now); lineLen = 0;
      }
    }
  }
}

void setup() {
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
#if CENTRAL_PCA9685
  addr = 0;
  pcaOk = pcaBegin();
  if (!pcaOk) Serial.println(F("ERRORE: PCA9685 non risponde (cavi SDA/SCL, alimentazione VCC, indirizzo)"));
#else
  addr = readAddress();
#endif
  seed = makeSeed(addr);
  randomSeed(seed);

  uint32_t now = millis();
  for (uint8_t i = 0; i < N_HEADS; i++) {
    Head &H = heads[i];
#if CENTRAL_PCA9685
    H.id = i + 1;
    H.lrOut.pin = PCA_CH[i][0];
    H.lidOut.pin = PCA_CH[i][1];
#else
    H.id = addr;
    H.lrOut.pin = PIN_LR;
    H.lidOut.pin = PIN_LID;
#endif
    H.begin(now);                         // posizione iniziale scritta PRIMA di agganciare
  }
  // avvio scaglionato: un servo alla volta, teste sfasate
  delay((CENTRAL_PCA9685 ? 0 : addr) * START_DELAY_PER_HEAD_MS + random(0, 400));
  for (uint8_t i = 0; i < N_HEADS; i++) {
    heads[i].lrOut.attach();  delay(ATTACH_STEP_MS);
    heads[i].lidOut.attach(); delay(ATTACH_STEP_MS);
  }
  now = millis();
  for (uint8_t i = 0; i < N_HEADS; i++) {
    heads[i].pickMood(now, false, false);
    heads[i].nextGazeAt = now + random(300, 2000) + i * 500;
    heads[i].scheduleBlink(now);
    heads[i].stillSince = now;
  }
  printStatus();
  lastUpdate = now;
}

void loop() {
  uint32_t now = millis();
  handleSerial(now);
  if (now - lastUpdate < UPDATE_MS) return;
  lastUpdate = now;
  readVoltage(now);
  updateLed(now);
  if (!pcaOk) return;
  for (uint8_t i = 0; i < N_HEADS; i++) heads[i].update(now, servoLow);
}
