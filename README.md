# Idra di Guerra

Elettronica e meccanica per il carro **"Idra di Guerra"** — Carnevale di Viareggio.

## Obiettivi
- **PCB (KiCad)**: scheda EyeNode per ogni testa (servo degli occhi), alimentazione da 2 × 6 V piombo in serie (12 V).
- **Firmware**: ogni testa muove gli occhi in modo autonomo e casuale, senza sincronia tra le teste.
- **Requisiti elettrici**: budget energetico, dimensionamento alimentatori, sezione cavi, protezioni.
- **Meccanica 3D**: occhi (Ø ≥ 50 mm), incavo/orbita, meccanismo di movimento, supporto servo.
- **Chassis**: contenitori per l'elettronica, cablaggio ordinato e manutenibile.

## Struttura
```
docs/                  requisiti, budget energetico, cablaggio
hardware/kicad/        progetto KiCad (schematico + PCB)
hardware/datasheets/   datasheet componenti
mechanical/eyes/       original/ = modelli sorgente, scaled/ = occhi ingranditi
mechanical/enclosures/ chassis per l'elettronica
mechanical/scripts/    script di generazione/scalatura dei modelli
firmware/              codice delle schede EyeNode (movimento casuale autonomo)
```

## Regola chiave per gli occhi
Il bulbo va ingrandito a **diametro ≥ 50 mm**, ma la **sede del servo resta in scala 1:1**
(i servomotori sono fissi e non cambiano dimensione).
