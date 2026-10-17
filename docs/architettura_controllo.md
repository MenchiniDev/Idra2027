# Architettura di controllo: un Nano per testa o un Nano centrale + PCA9685?

Contesto: 4 teste, ognuna con 2 MG995 (sx/dx + palpebre); batteria 12 V (2 × 6 V piombo) nel
vano tecnico alla base; teste a 4–5 m di cavo dalla base. Il firmware `firmware/EyeNode_2servo`
supporta entrambe le soluzioni (`CENTRAL_PCA9685` in `config.h`).

> Il chip è il **PCA9685** (16 canali PWM, I2C), venduto come modulo blu "16-channel 12-bit
> PWM/Servo driver" a 3–6 €.

## Le due soluzioni

```
A) UN NANO PER TESTA (EyeNode attuale)
   BASE: batteria 12 V ─ fusibili ──── 2 × 1.5 mm² (12 V) ────► TESTA: DC-DC 12→6 V + EyeNode (Nano) ─► 2 servo
   (x4 rami)                                                       tutto dentro la testa

B) NANO CENTRALE + PCA9685
   BASE: batteria 12 V ─ DC-DC 12→6 V (x4 o 1 grande) ─ 2 × 2.5 mm² (6 V) ──────────────► TESTA: 2 servo
         Nano ─ I2C (corto, dentro la scatola) ─ PCA9685 ─ cavo segnali (2 SIG + GND) ──►      + condensatore
                                                                                        nella testa niente elettronica
```

## Costi (4 teste, stime come in `lista_spesa.md`)

| Voce | A: Nano per testa | B: Nano centrale + PCA9685 |
|---|---|---|
| Arduino Nano | 4 × ~6 € = 24 € | 1 × 6 € |
| PCA9685 | — | 2 × 5 € = 10 € (uno di scorta) |
| PCB / schede | 4 EyeNode + componenti ≈ 45 € | 1 scheda base (semplice) ≈ 15 € |
| DC-DC 12→6 V | 4 × ~12 € = 48 € (nelle teste) | uguale, ma nella scatola alla base (oppure 1 da 20 A ≈ 30 €) |
| Cavo alimentazione 4 × 5 m | 2 × 1.5 mm² ≈ 25 € | 2 × 2.5 mm² ≈ 35 € |
| Cavo segnali 4 × 5 m | — | 3–4 poli twistato/schermato ≈ 20 € |
| Connettori stagni in più | — | ≈ 10 € |
| **Totale** | **≈ 140 €** | **≈ 115–145 €** |

**Il risparmio di B è piccolo: 0–25 € su un budget di ~600–700 €.** La scelta va fatta sugli aspetti
tecnici, non sul prezzo.

## È fattibile B? Sì, con qualche accorgimento

### Segnale PWM su 4–5 m: sì
Il segnale servo è lento (un impulso di 1–2 ms ogni 20 ms), quindi la lunghezza del cavo non è un
problema in sé: 5 m di cavo hanno ~0.5 nF, che arrotondano i fronti di pochi µs (il servo legge
differenze di ~5–10 µs, quindi ±1 grado al massimo). I rischi veri sono due:
- **disturbi** (motori, luci, inverter del carro): usare un cavo **twistato o schermato**, con il
  GND dei segnali insieme ai segnali; lo schermo collegato a GND **solo alla base**;
- **spostamento del GND**: la corrente dei servo che torna alla base sul filo di massa sposta il
  riferimento del segnale di I × R. Con 2.5 mm² e 5 A di picco: 0.035 Ω × 5 A ≈ 0.18 V. Con il
  PCA9685 alimentato a **5 V** (VCC = 5 V, livelli logici 0/5 V) il margine è ampio (il servo commuta
  attorno a 1.5–2.5 V).

Il modulo PCA9685 ha già resistenze da 220 Ω in serie sulle uscite, che smorzano le riflessioni.
**Non** portare l'I2C su per il collo: l'I2C su 5 m non è affidabile. Il PCA9685 sta alla base,
vicino al Nano, e su per il collo vanno solo i segnali PWM.

### Alimentazione dei servo dalla base a 4–5 m: sì, ma cavo più grosso
Corrente per testa (2 MG995): ~1–1.5 A tipica in movimento, ~5 A di picco (entrambi in stallo).
Caduta sul cavo, andata + ritorno = 10 m:

| Sezione | R (10 m) | Caduta a 1.5 A | Caduta a 5 A (picco) |
|---|---|---|---|
| 1.5 mm² | 0.117 Ω | 0.18 V (3 %) | 0.58 V (10 %) |
| **2.5 mm²** | **0.070 Ω** | **0.11 V (2 %)** | **0.35 V (6 %)** |

Con 2.5 mm², il DC-DC regolato a **6.3–6.5 V** alla base (l'MG995 accetta fino a 7.2 V) e un
**condensatore da 2200 µF / 10 V** nella testa, vicino ai servo (copre gli spunti), i servo vedono
sempre 5.9–6.4 V. Va bene.

Alternativa ibrida: continuare a portare **12 V** nella testa con il DC-DC lì, come in A, e mandare
su solo i segnali dalla base. Dimezza la corrente nel cavo, ma rimette elettronica nella testa.

## Pro e contro

| | A: Nano per testa | B: Nano centrale + PCA9685 |
|---|---|---|
| Fili su per ogni collo | 2 (12 V) | 2 potenza + 3 segnali (o un cavo multipolare unico) |
| Un guasto ferma… | solo quella testa | **tutte le teste** (Nano, PCA o alimentazione centrale) |
| Manutenzione durante il Carnevale | schede dentro le teste, a 4–5 m d'altezza | **tutta l'elettronica in una scatola alla base**, nelle teste solo servo |
| Aggiornare il firmware | 4 schede da raggiungere | 1 sola scheda |
| Coreografie (tutte le teste guardano lo stesso punto, "risposta" a un pulsante, ecc.) | servirebbe un bus tra le teste | **facili**: un solo programma vede tutte le teste |
| Rischio tecnico | basso (cavi corti) | medio: cavi segnale lunghi, da provare sul banco |
| Lavoro di progettazione | EyeNode esiste già (da semplificare a 2 servo) | scheda base nuova, ma semplice |

## Consiglio
Le due soluzioni costano quasi uguale. **B è la più comoda sul carro**: tutta l'elettronica in un
punto raggiungibile, nelle teste solo servo e un condensatore, un solo firmware, e la possibilità di
far muovere le teste in modo coordinato quando serve. Il prezzo da pagare è un punto di guasto unico
(si mitiga con un Nano e un PCA9685 di scorta già programmati, da sostituire in 2 minuti) e la
necessità di **provare prima sul banco** il segnale su 5 m di cavo.

Prova da fare prima di decidere (vedi `docs/TODO.md`): un MG995 alimentato a 6 V con 5 m di cavo
2 × 2.5 mm² e il segnale su 5 m di cavo twistato, comandato dal Pi o da un Nano + PCA9685. Se il servo
è stabile (nessun tremolio in più rispetto al cavo corto) anche con un altro motore acceso vicino,
B è confermata.
