# Collaudo servo su Raspberry Pi

`servo_test.py` muove un servo (MG995 o MG90S) attraverso una sequenza di prove e chiede
all'operatore di confermare ogni passo; alla fine stampa **BUONO** o **DA SCARTARE**.

## Collegamenti
| Filo servo | Dove |
|---|---|
| arancione / giallo (segnale) | GPIO13 = pin fisico 33 (il GPIO18 è riservato alla scheda audio WM8960 nel config.txt del Pi) |
| marrone / nero (GND) | GND dell'alimentatore **e** un GND del Pi (es. pin 6) |
| rosso (V+) | + alimentatore esterno 5–6 V, almeno 3 A (es. 4 stilo AA, pacco NiMH 6 V, alimentatore da banco) |

Non alimentare un MG995 dal pin 5 V del Pi: allo spunto assorbe 1–2.5 A e il Pi si riavvia.
Il segnale a 3.3 V del Pi va bene per MG995/MG90S.

## Uso
```bash
sudo apt install -y python3-gpiozero python3-lgpio   # di solito già presenti
python3 servo_test.py            # test automatico
python3 servo_test.py --manual   # comandi a mano: 0-180, u1500, s, o, q
```
Gli estremi di default sono 1000–2000 µs (sicuri per tutti i servo). Per vedere tutta la corsa di
un MG995: `--min-us 500 --max-us 2500` (attenzione: alcuni esemplari vanno a fine corsa e ronzano).

## Segni di un MG995 da scartare
- non si muove, oppure si muove solo in un verso;
- scatti, punti duri, rumore di ingranaggi rotti a metà corsa;
- trema o "caccia" da fermo in modo evidente (i MG995 economici hanno una zona morta larga: un
  piccolo tremolio è purtroppo normale);
- scalda molto in pochi secondi senza carico;
- con un multimetro in serie sul + : più di ~0.3 A da fermo senza carico.
