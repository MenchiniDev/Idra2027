# Requisiti — Idra di Guerra

> Bozza: i valori marcati **TBD** vanno confermati.

## Servomotori
| Voce | Valore |
|---|---|
| Modello servo | MG90S (metal gear) — SG90 sconsigliati |
| N. occhi | 7 (3 coppie + 1 singolo) → 21 servo, 4 schede EyeNode |
| Servo per occhio | 3 (sx/dx, su/giù, palpebre) |
| Tensione nominale | 4.8–6 V (alimentazione servo 6 V da DC-DC) |
| Movimento | autonomo e casuale per ogni testa, nessuna sincronia |
| Corrente di stallo per servo | ~0.7–1 A (da verificare su datasheet del lotto acquistato) |

## Alimentazione
- 2 batterie 6 V piombo **in serie** = 12 V, 30 Ah (AGM/VRLA consigliate).
- Fusibile generale entro 30 cm dal + batteria, fusibile da 5 A per ogni testa, protezione sottotensione.

## Budget energetico
- Corrente di picco = N_servo × I_stallo (dimensionare alimentatore su questo valore + 25% margine).
- Distribuzione per rami con fusibile dedicato.

## Cablaggio
- Sezione cavi in funzione di corrente e lunghezza (caduta di tensione < 3%).
- Connettori bloccabili (vibrazioni del carro), cavi segnale schermati sulle tratte lunghe.

## Ambiente
- Esterno, pioggia/umidità, vibrazioni: contenitori almeno IP54, PCB con conformal coating.

Lista della spesa: [lista_spesa.md](lista_spesa.md)

Dettagli completi (architettura, bilancio energetico, cavi, fusibili): [electronics.md](electronics.md)
