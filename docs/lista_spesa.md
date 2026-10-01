# Lista della spesa — L'Idra 2027

Per 4 teste (3 coppie + 1 singolo = 7 occhi, 21 servo), alimentazione 2 × 6 V piombo in serie.
Le quantità includono già qualche **ricambio** (colonna "di cui ricambi").
Prezzi = **stima indicativa** in €, IVA inclusa, da negozi online tipo Amazon/AliExpress/elettronica
generica: servono per farsi un'idea del budget, non sono preventivi.

> **Cavi: lunghezze stimate.** Ho assunto ≤ 5 m dal vano tecnico a ogni testa. Prima di comprare
> misurare il percorso reale di ogni collo (+ 1 m di scorta). Se un collo supera i 5 m, quel ramo va
> in 2 × 2.5 mm² invece di 2 × 1.5 mm².

## 1. Alimentazione (vano tecnico nel corpo)
| # | Articolo | Specifica | Q.tà | di cui ricambi | € stima |
|---|---|---|---|---|---|
| 1 | Batterie | 6 V 30 Ah piombo AGM/VRLA, **già disponibili** — da collegare in **serie** | 2 | — | — |
| 2 | Portafusibile generale stagno | per fusibile a lama ATO (o MIDI), con cavo 4 mm² | 1 | — | 6–10 |
| 3 | Fusibili ATO 20 A | lama standard | 3 | 2 | 3 |
| 4 | Sezionatore generale | stacca-batteria rotativo ≥ 30 A, stagno | 1 | — | 15–25 |
| 5 | Modulo LVD (protezione sottotensione) | 12 V, ≥ 20 A, stacco ~11.5 V / riattacco ~12.5 V, regolabile | 1 | — | 15–25 |
| 6 | Blocco fusibili | 6 vie ATO **con barra negativa integrata** e coperchio (tipo nautico) — *oppure* 4 portafusibili ATO in linea stagni | 1 | — | 15–25 |
| 7 | Fusibili ATO 5 A | rami verso le teste | 8 | 4 | 3 |
| 8 | Caricabatterie | 12 V piombo/AGM, 3–6 A, con mantenimento | 1 | — | 30–50 |
| 9 | Presa di ricarica (opz.) | presa stagna 2 poli (tipo SAE o Anderson 50 A) da pannello | 1 | — | 5–10 |
| 10 | Scatola vano tecnico | IP65 ~300 × 200 × 150 mm, o cassetta batterie con cinghie | 1 | — | 20–35 |

## 2. Elettronica in ogni testa
| # | Articolo | Specifica | Q.tà | di cui ricambi | € stima |
|---|---|---|---|---|---|
| 11 | Convertitore DC-DC | 12 V → 6 V, **≥ 10 A**, ingresso almeno 9–16 V, resinato/impermeabile | 5 | 1 | 50–75 |
| 12 | Servo MG90S | **metal gear** (non SG90) | 25 | 4 | 75–100 |
| 13 | Prolunghe servo | 3 fili JR/Futaba, 30–50 cm (misurare dalla scheda agli occhi) | 25 | 4 | 10–15 |
| 14 | Fusibili a lama **mini** 7.5 A | per F2 sulla scheda (teste 1–3) | 6 | 3 | 2 |
| 15 | Fusibili a lama **mini** 5 A | per F2 sulla scheda (testa 4) | 2 | 1 | 1 |
| 16 | Scatola per scheda + DC-DC | IP65 ~150 × 120 × 70 mm (o contenitore stampato 3D) | 4 | — | 25–40 |
| 17 | Pressacavi | PG7 (cavi servo) + PG9 (alimentazione), kit assortito | 1 kit | — | 8 |
| 18 | Morsetti a leva Wago 221-413 | per dividere il 12 V tra DC-DC e J1 nella testa | 10 | 2 | 6 |

## 3. Scheda EyeNode (componenti per 5 schede: 4 + 1 ricambio)
| # | Articolo | Rif. | Footprint / tipo | Q.tà | € stima |
|---|---|---|---|---|---|
| 19 | PCB EyeNode v0.2 | — | JLCPCB, 2 strati, **rame 2 oz**, 110 × 90 mm (file `fab/EyeNode_gerber_JLCPCB.zip`) | 5 (minimo ordine) | 25–45 con spedizione |
| 20 | Arduino Nano v3 | A1 | ATmega328P, USB mini-B o C | 5 | 25–40 |
| 21 | Strip femmina 1 × 15, passo 2.54 | per A1 | per rendere il Nano estraibile | 10 | 3 |
| 22 | Regolatore RECOM R-78E5.0-0.5 | U1 | THT SIP3 | 5 | 20 |
| 23 | Condensatore elettrolitico 1000 µF **16 V** low-ESR | C1, C2 | radiale Ø10 mm, passo 5 mm | 10 | 5 |
| 24 | Condensatore ceramico 100 nF | C3 | SMD 1206 | 10 | 1 |
| 25 | Condensatore ceramico 10 µF 50 V | C4 | SMD 1206 | 10 | 2 |
| 26 | Condensatore ceramico 10 µF 16 V | C5 | SMD 1206 | 10 | 1 |
| 27 | Diodo Schottky SS34 | D1 | SMA | 10 | 1 |
| 28 | Diodo Schottky SS54 | D2 | SMC | 10 | 2 |
| 29 | LED verde | D3 | SMD 1206 | 10 | 1 |
| 30 | LED blu | D4 | SMD 1206 | 10 | 1 |
| 31 | Polyfuse 0.5 A | F1 | SMD 1812 | 10 | 2 |
| 32 | Portafusibile lama mini Keystone 3568 | F2 | THT | 5 | 6 |
| 33 | Morsetto a vite 2 poli passo 5.08 (Phoenix MKDS 1,5/2) | J1, J2 | THT | 10 | 4 |
| 34 | Strip maschio 1 × 40, passo 2.54 | J3–J8, J11 | da tagliare a 3 e 5 pin | 5 | 2 |
| 35 | Resistenza 220 Ω | R1–R6 | SMD 1206 | 50 | 1 |
| 36 | Resistenza 1 kΩ | R10, R13 | SMD 1206 | 20 | 1 |
| 37 | Resistenza 10 kΩ | R11, R12 | SMD 1206 | 20 | 1 |
| 38 | DIP switch 4 vie | SW1 | THT passo 2.54 | 5 | 3 |
| 39 | Distanziali M3 10 mm + viti | fori angoli | nylon o ottone | 20 | 4 |

*Facoltativo, misura batteria nel firmware:* resistenze 47 kΩ e 10 kΩ (¼ W), 5 + 5.
*Alternativa:* far montare i componenti SMD direttamente a JLCPCB (servizio di assemblaggio) usando
`EyeNode_BOM.csv` e `EyeNode_pos.csv`; restano da saldare a mano solo i componenti a foro passante.

## 4. Cavi e materiale di cablaggio
| # | Articolo | Specifica | Q.tà | Uso | € stima |
|---|---|---|---|---|---|
| 40 | Cavo unipolare **4 mm²** rosso | flessibile (FS17/H07V-K) | 3 m | batteria → fusibile → sezionatore → LVD → blocco fusibili | 5 |
| 41 | Cavo unipolare **4 mm²** nero | flessibile | 3 m | ritorno negativo + **ponticello serie** tra le batterie | 5 |
| 42 | Cavo bipolare **2 × 1.5 mm²** rosso/nero | piattina o cavo con guaina (FROR) | 25 m | 4 rami da ~5 m verso le teste + DC-DC → J2 | 25–35 |
| 43 | Cavo bipolare 2 × 2.5 mm² | solo se un collo supera 5 m | a misura | ramo lungo | — |
| 44 | Cavo 3 × 0.5 mm² (o prolunghe servo da 1–2 m) | solo se un servo è a più di 1 m dalla scheda | a misura | prolunghe lunghe | — |
| 45 | Capicorda ad occhiello 4 mm² | foro adatto ai poli batteria e al sezionatore (M5/M6/M8, verificare) | 10 | poli batteria, sezionatore | 3 |
| 46 | Faston femmina isolati 6.3 mm, 4 mm² | solo se le batterie hanno poli faston | 6 | poli batteria | 2 |
| 47 | Puntalini isolati | kit assortito 0.5 – 4 mm² | 1 kit | tutti i morsetti a vite | 8 |
| 48 | Connettori stagni 2 poli, maschio + femmina | tipo Superseal / Deutsch DT, per 1.5 mm² | 5 coppie | staccare ogni testa alla base del collo | 12–20 |
| 49 | Guaina termorestringente | kit assortito, con colla | 1 kit | giunzioni e connettori | 8 |
| 50 | Tubo corrugato spiralato | Ø 10–13 mm | 20 m | protezione cavi nei colli | 10–15 |
| 51 | Fascette | 200 mm + 300 mm, nere anti-UV | 200 | fissaggio cavi ogni 20–30 cm | 6 |
| 52 | Basette per fascette | adesive o a vite | 50 | punti di fissaggio sul telaio | 5 |
| 53 | Cavo USB (mini-B o C, come i Nano) | — | 1 | programmazione | 3 |

## 5. Meccanica occhi (dipende dalla taglia scelta)
| # | Articolo | D50 | D70 | D90 | Q.tà |
|---|---|---|---|---|---|
| 54 | Filamento PETG (o PLA+) | ~1 kg | ~2 kg | ~3 kg | — |
| 55 | Vite snodo + inserto filettato a caldo | M4 | M6 | M8 | 7 + 3 ricambi |
| 56 | Filo armonico (acciaio) per tiranti occhio | Ø 1.5 mm | Ø 2.0 mm | Ø 2.5 mm | 2 m |
| 57 | Viti M2 autofilettanti 8–12 mm | per LidCrank, HornExtender, tiranti palpebre | | | 100 |
| 58 | Viti fissaggio piastre al telaio | Ø foro 5 / 7 / 9 mm | | | 30 |

## Riepilogo budget indicativo
| Gruppo | € stima |
|---|---|
| 1. Alimentazione (batterie escluse) | ~110–185 |
| 2. Elettronica teste | ~175–245 |
| 3. Scheda EyeNode × 5 | ~110–150 |
| 4. Cavi e cablaggio | ~90–115 |
| 5. Meccanica (D70) | ~50–80 |
| **Totale** | **~545–775 €** |

## Attrezzi (se mancano)
Saldatore con punta fine + stagno 0.5 mm e flussante; **crimpatrice** per capicorda e puntalini;
spelafili; pistola termica; multimetro; stampante 3D.
