# TODO — occhi EyeMech (idra_version, poi D85)

Obiettivo: verificare meccanica + codice degli occhi EyeMech a 4 servo SG90/MG90S (X, Y, palpebre sx,
palpebre dx), prima nella versione di prova in scala di Will, poi nella D85; poi passare al PCB.
Dettagli: `docs/mechanical_eyes.md`.

## 1. Servo
- [ ] Collaudare i servo con alimentazione **esterna** 5–6 V (GND in comune col Pi):
      `ssh -p 2222 pi@192.168.3.103` → `python3 ~/idra/servo_test.py` (segnale su pin 33)
- [ ] Mai più servo alimentati dal 5 V del Pi (il Pi si riavvia, rischio SD/OctoPrint)
- [ ] Misurare un SG90/MG90S col calibro e confrontare con `SG_*` in `mechanical/scripts/generate_eyemech.py`
      (corpo 22.8 × 12.4, orecchie 32.6, fori 27.8, fondo → orecchie 15.9, fondo → faccia superiore 22.7)

## 2. idra_version (`mechanical/eyes/idra_version/`)
- [ ] Stampare tutti i pezzi (lista in `docs/mechanical_eyes.md` → "idra_version")
- [ ] Viti: 2 × M2×8 (PinB) + 2 × M2×5 (rondelle) + quelle della guida di Will
- [ ] Montare come nella guida di Will, solo i servo anteriori delle palpebre
- [ ] Muovere a mano (servo staccati): palpebre che si chiudono insieme, niente punti duri
- [ ] Prova col firmware a 4 servo: corse, calibrazione (90° = palpebre chiuse), 30 min di movimento casuale

## 3. Versione D85 (`mechanical/eyes/eyemech_D85/`)
- [ ] Prima: provare una sede 1:1 e una squadretta col servo vero
- [ ] Stampare gli 8 piatti di `eyemech_D85/bambu_A1/` (≈ 30 h, ≈ 0.86 kg PLA)
- [ ] Controllare al montaggio che i codoli delle squadrette X/Y non tocchino il mozzo ingranaggi
- [ ] Prova di movimento: MG90S consigliati (pezzi ~19 volte più pesanti dell'originale)

## 4. Scelta architettura (vedi `docs/architettura_controllo.md`)
- [ ] Prova sul banco: servo con 5 m di cavo 2 × 2.5 mm² per l'alimentazione (6 V) e 5 m di cavo
      twistato per il segnale; confrontare il tremolio con quello a cavo corto, anche con un altro
      motore acceso vicino
- [ ] Se va bene → Nano centrale + PCA9685 alla base (`CENTRAL_PCA9685 1`), altrimenti un Nano per testa
- [ ] Comprare un PCA9685 (meglio 2) se si sceglie la soluzione centrale

## 5. Poi: PCB
- [ ] Aggiornare requisiti e budget energetico: 4 MG90S per coppia di occhi
- [ ] Firmware a 4 servo (`EyeNode_2servo` ne gestisce 2)
- [ ] Secondo l'architettura scelta: EyeNode per ogni testa, oppure una scheda base unica
      (Nano + PCA9685 + fusibili per ramo + morsetti per i colli)
- [ ] Aggiornare `docs/lista_spesa.md`
