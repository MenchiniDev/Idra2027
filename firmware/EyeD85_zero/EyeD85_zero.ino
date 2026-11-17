// =====================================================================
//  EyeD85_zero — occhi EyeMech D85: tutti i servo a zero + taratura
// =====================================================================
//  Scheda: ESP8266 (modulo ESP-12F, es. NodeMCU o Wemos D1 mini) con una
//  PCA9685 su I2C (SDA = GPIO4/D2, SCL = GPIO5/D1).
//
//  All'accensione porta i 4 servo a 90 gradi, la posizione in cui si
//  montano le squadrette (come il calibrate() di Will):
//    X, Y     : occhi dritti davanti
//    palpebre : chiuse
//  Poi, dal Monitor seriale, si muove un servo alla volta per trovare i
//  limiti da scrivere in EyeD85_random/config.h.
//
//  Canali PCA9685 (0-based): 4 = X (sx/dx), 6 = Y (su/giu'),
//  10 = palpebre sinistra, 11 = palpebre destra.
//  Gradi come nel codice di Will (Arduino Servo): 0..180 = 544..2400 us.
//
//  Seriale 115200, comandi terminati da Invio:
//    z         tutti i servo a 90 gradi (zero)
//    x y s d   seleziona il servo: X, Y, palpebre Sinistra, palpebre Destra
//    x75       servo X a 75 gradi (idem y.., s.., d..; decimali: x75.5)
//    + / -     servo selezionato +1 / -1 grado   (++ / -- = 5 gradi)
//    1 2 3     memorizza la posizione del servo selezionato come
//                1 = estremo -1: sinistra di chi guarda / basso / palpebre CHIUSE
//                2 = centro (solo X e Y)
//                3 = estremo +1: destra di chi guarda / alto / palpebre APERTE
//    t130,136  sequenza: il servo selezionato passa per i valori elencati
//              (fino a 12), TOUR_MS su ognuno, andata e ritorno senza fine
//              (o TOUR_PASSES volte, poi resta sul primo). Qualsiasi altro
//              comando (tranne ?) la interrompe
//    p         stampa le righe da incollare in EyeD85_random/config.h
//    o         spegne gli impulsi: servo liberi, si girano a mano
//    ?         stato
//  I servo si spostano a velocita' limitata (SLEW_DEG_S), anche nei salti.
//  Restare DENTRO la corsa libera: un servo contro un fermo va in stallo,
//  assorbe ~0.7 A (SG90) e scalda.
//
//  Librerie: solo Wire (inclusa nel core).
// =====================================================================
#include <Wire.h>
#if defined(ESP8266)
  #include <ESP8266WiFi.h>
#endif

// ----------------------------------------------------------- hardware
const uint8_t  PIN_SDA = 4;                 // GPIO4 = D2 (NodeMCU, D1 mini)
const uint8_t  PIN_SCL = 5;                 // GPIO5 = D1
const uint8_t  PCA_ADDR = 0x40;             // indirizzo I2C della PCA9685 (default)
const float    PCA_OSC_HZ = 25000000.0f;    // oscillatore interno (come EyeD85_random)
const float    US_0 = 544.0f, US_180 = 2400.0f;   // gradi -> microsecondi
const float    ZERO_DEG = 90.0f;
const float    SLEW_DEG_S = 60.0f;          // velocita' massima degli spostamenti
const uint16_t ATTACH_STEP_MS = 250;        // avvio un servo alla volta
const uint16_t UPDATE_MS = 10;
const uint16_t TOUR_MS = 1000;              // tempo su ogni valore della sequenza 't'
const uint8_t  TOUR_PASSES = 0;             // andate e ritorni della sequenza (0 = senza fine)

// Servo. mark[] = -1 / centro / +1 memorizzati, in partenza i valori di
// EyeD85_random/config.h (per le palpebre il centro non si usa).
struct Joint {
  const char *name;
  char key;
  uint8_t ch;
  float mark[3];
  float target, cur;
  int lastTicks;
};
Joint J[] = {
  { "X (sx/dx)",         'x', 4,  { 54.0f, 90.0f, 139.0f }, ZERO_DEG, ZERO_DEG, -1 },
  { "Y (su/giu')",       'y', 6,  { 53.0f, 90.0f, 109.0f }, ZERO_DEG, ZERO_DEG, -1 },
  { "palpebre sinistra", 's', 10, { 90.0f, 90.0f, 170.0f }, ZERO_DEG, ZERO_DEG, -1 },
  { "palpebre destra",   'd', 11, { 90.0f, 90.0f,  10.0f }, ZERO_DEG, ZERO_DEG, -1 },
};
const uint8_t N_JOINTS = sizeof(J) / sizeof(J[0]);
const uint8_t N_AXES = 2;                   // i primi due sono assi, gli altri palpebre

uint8_t sel = 0;
bool pulses = false, pcaOk = false;
uint32_t lastUpdate = 0, lastCharAt = 0, lastPcaTry = 0;
char line[64];
uint8_t lineLen = 0;

// Sequenza 't': valori del servo tourSel, indice del prossimo e verso
float tour[12];
uint8_t tourLen = 0, tourSel = 0, tourIdx = 0, tourPass = 0;
int8_t tourDir = 1;
uint32_t tourNext = 0;

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

float degToUs(float deg) { return US_0 + (US_180 - US_0) * deg / 180.0f; }

void writeJoint(Joint &j) {
  int ticks = (int)(degToUs(j.cur) * 4096.0f * pcaHz / 1000000.0f + 0.5f);
  if (ticks == j.lastTicks) return;
  j.lastTicks = ticks;
  pcaChannel(j.ch, 0, ticks);
}

void pulsesOff() {
  for (uint8_t i = 0; i < N_JOINTS; i++) { pcaChannel(J[i].ch, 0, 0x1000); J[i].lastTicks = -1; }   // FULL_OFF
  pulses = false;
}

// ----------------------------------------------------------- seriale
void printJoint(const Joint &j) {
  Serial.print(j.name); Serial.print(F(" (canale ")); Serial.print(j.ch); Serial.print(F("): "));
  Serial.print(j.target, 1); Serial.print(F(" gradi = "));
  Serial.print(degToUs(j.target), 0); Serial.println(F(" us"));
}

void printStatus() {
  Serial.print(F("EyeD85_zero  PCA9685 0x")); Serial.print(PCA_ADDR, HEX);
  Serial.print(pcaOk ? F(" ok") : F(" NON TROVATA"));
  Serial.println(pulses ? F("  impulsi ON") : F("  impulsi OFF (servo liberi)"));
  for (uint8_t i = 0; i < N_JOINTS; i++) {
    Serial.print(i == sel ? F(" > ") : F("   ")); printJoint(J[i]);
  }
}

void printConfig() {
  Serial.println(F("// --- da incollare in EyeD85_random/config.h ---"));
  for (uint8_t i = 0; i < N_JOINTS; i++) {
    const Joint &j = J[i];
    static const char *const VAR[] = { "CAL_X    ", "CAL_Y    ", "CAL_LID_L", "CAL_LID_R" };
    Serial.print(i < N_AXES ? F("const AxisCal ") : F("const LidCal  "));
    Serial.print(VAR[i]); Serial.print(F(" = { "));
    Serial.print(j.mark[0], 1); Serial.print(F("f, "));
    if (i < N_AXES) { Serial.print(j.mark[1], 1); Serial.print(F("f, ")); }
    Serial.print(j.mark[2], 1); Serial.println(F("f };"));
  }
}

Joint *jointByKey(char c) {
  for (uint8_t i = 0; i < N_JOINTS; i++) if (J[i].key == c) { sel = i; return &J[i]; }
  return nullptr;
}

void moveTo(Joint &j, float deg) {
  j.target = constrain(deg, 0.0f, 180.0f);
  pulses = true;
  printJoint(j);
}

void command() {
  char c = line[0];
  Joint &S = J[sel];
  if (c != '?') tourLen = 0;                 // un comando interrompe la sequenza
  if (c == 'z') {
    for (uint8_t i = 0; i < N_JOINTS; i++) J[i].target = ZERO_DEG;
    pulses = true;
    Serial.println(F("ZERO: tutti i servo a 90 gradi (X/Y dritti, palpebre chiuse)"));
  } else if (Joint *j = jointByKey(c)) {
    if (line[1]) moveTo(*j, atof(line + 1));
    else { Serial.print(F("selezionato: ")); printJoint(*j); }
  } else if (c == '+' || c == '-') {
    float step = line[1] == c ? 5.0f : 1.0f;
    moveTo(S, S.target + (c == '+' ? step : -step));
  } else if (c >= '1' && c <= '3') {
    uint8_t k = c - '1';
    if (k == 1 && sel >= N_AXES) { Serial.println(F("le palpebre non hanno centro: 1 = chiuse, 3 = aperte")); return; }
    S.mark[k] = S.target;
    static const char *const AXIS_MARK[] = { "estremo -1", "centro", "estremo +1" };
    static const char *const LID_MARK[] = { "CHIUSE", "", "APERTE" };
    Serial.print(S.name); Serial.print(F(": ")); Serial.print(sel < N_AXES ? AXIS_MARK[k] : LID_MARK[k]);
    Serial.print(F(" = ")); Serial.print(S.target, 1); Serial.println(F(" gradi"));
  } else if (c == 't') {
    char *p = line + 1;
    uint8_t n = 0;
    while (*p && n < sizeof(tour) / sizeof(tour[0])) {
      char *end;
      double v = strtod(p, &end);            // fuori da constrain(): e' una macro, rileggerebbe
      if (end == p) break;                   // non e' un numero
      tour[n++] = constrain(v, 0.0, 180.0);
      p = end;
      if (*p == ',') p++; else break;
    }
    if (n < 2) { Serial.println(F("sequenza: almeno 2 valori, es. t130,136,142")); return; }
    tourLen = n; tourSel = sel; tourIdx = 0; tourDir = 1; tourPass = 0; tourNext = millis();
    pulses = true;
    Serial.print(F("sequenza ")); Serial.print(S.name); Serial.print(F(": ")); Serial.print(n);
    Serial.print(F(" valori, ")); Serial.print(TOUR_MS); Serial.println(F(" ms ciascuno"));
  } else if (c == 'p') {
    printConfig();
  } else if (c == 'o') {
    pulsesOff();
    Serial.println(F("impulsi OFF: servo liberi"));
  } else if (c == '?') {
    printStatus();
  } else {
    Serial.println(F("comandi: z | x y s d (seleziona) | x75 y90 s170 d10 | + - ++ -- | 1 2 3 (memorizza) | t130,136 (sequenza) | p | o | ?"));
  }
}

// Comandi terminati da Invio; senza fine riga partono dopo 80 ms di silenzio
void handleSerial(uint32_t now) {
  while (Serial.available()) {
    char c = Serial.read();
    lastCharAt = now;
    if (c == '\n' || c == '\r') {
      if (lineLen) { line[lineLen] = 0; command(); lineLen = 0; }
    } else if (c != ' ' && lineLen < sizeof(line) - 1) {
      line[lineLen++] = c;
    }
  }
  if (lineLen && now - lastCharAt > 80) { line[lineLen] = 0; command(); lineLen = 0; }
}

// Sequenza 't': un valore ogni TOUR_MS, andata e ritorno
void tourStep(uint32_t now) {
  if (!tourLen || (int32_t)(now - tourNext) < 0) return;
  Joint &j = J[tourSel];
  j.target = tour[tourIdx];
  Serial.print(F("sequenza: ")); Serial.print(j.name); Serial.print(F(" = ")); Serial.println(j.target, 1);
  tourNext = now + TOUR_MS;
  if (tourIdx + tourDir < 0 || tourIdx + tourDir >= tourLen) {
    tourDir = -tourDir;
    if (tourDir > 0 && TOUR_PASSES && ++tourPass >= TOUR_PASSES) { tourLen = 0; Serial.println(F("sequenza finita")); return; }
  }
  tourIdx += tourDir;
}

// ----------------------------------------------------------- main
// Posizione attuale (90 gradi all'accensione), un servo alla volta: meno
// spunto sull'alimentazione
void startServos() {
  for (uint8_t i = 0; i < N_JOINTS; i++) {
    J[i].cur = J[i].target;
    J[i].lastTicks = -1;
    writeJoint(J[i]);
    delay(ATTACH_STEP_MS);
  }
  pulses = true;
}

void setup() {
  Serial.begin(115200);
#if defined(ESP8266)
  WiFi.mode(WIFI_OFF);                       // niente WiFi: meno consumo e niente riconnessioni
#endif
  delay(200);
  Serial.println();
  Serial.println(F("EyeD85_zero: servo a 90 gradi per il montaggio delle squadrette"));
  pcaOk = pcaBegin();
  if (pcaOk) startServos();
  else Serial.println(F("ERRORE: PCA9685 non risponde (cavi SDA/SCL, VCC 3.3 V, GND comune, indirizzo)"));
  printStatus();
  Serial.println(F("'?' stato, 'p' righe per config.h, 'h' aiuto"));
  lastUpdate = lastPcaTry = millis();
}

void loop() {
  uint32_t now = millis();
  handleSerial(now);
  if (now - lastUpdate < UPDATE_MS) return;
  float maxStep = SLEW_DEG_S * (now - lastUpdate) / 1000.0f;
  lastUpdate = now;
  if (!pcaOk) {                              // riprova ogni 2 s (es. PCA9685 collegata dopo)
    if (now - lastPcaTry > 2000) {
      lastPcaTry = now;
      pcaOk = pcaBegin();
      if (pcaOk) { Serial.println(F("PCA9685 trovata")); startServos(); }
    }
    return;
  }
  if (!pulses) return;
  tourStep(now);
  for (uint8_t i = 0; i < N_JOINTS; i++) {
    Joint &j = J[i];
    j.cur += constrain(j.target - j.cur, -maxStep, maxStep);
    writeJoint(j);
  }
}

