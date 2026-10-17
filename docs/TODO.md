# TODO — prova occhi a 2 servo MG995 (taglia D50)

Stato al 4/10/2026. Obiettivo: verificare meccanica + codice della coppia di occhi a 2 servo,
poi passare al PCB.

File di stampa: `mechanical/print/MG995_D50/` (progetti Bambu Studio).
Istruzioni di montaggio: `docs/mechanical_eyes.md` → "Versione COPPIA a 2 servo MG995".

## 1. Servo
- [ ] Ricollaudare il **2° MG995** con alimentazione **esterna** 5–6 V (GND in comune col Pi):
      `ssh -p 2222 pi@192.168.3.103` → `python3 ~/idra/servo_test.py` (segnale su pin 33)
- [ ] (facoltativo) collaudare anche gli altri 3 MG995 → servono ricambi
- [ ] Mai più servo alimentati dal 5 V del Pi (il Pi si riavvia, rischio SD/OctoPrint)

## 2. Provino sede MG995
- [ ] Stampare `Piatto_0_PROVA_sede_MG995.3mf` (nuova versione con asole cavo a tutta altezza)
- [ ] Il servo scende finché le orecchie appoggiano sulla piastrina, il cavo esce dall'asola
- [ ] I 4 fori coincidono con le asole delle orecchie (viti M3 × 12 + dado)
- [ ] Se qualcosa non torna: misurare col calibro (larghezza orecchia-orecchia, fondo → faccia
      inferiore orecchie, fondo → faccia squadretta) e correggere `MG995_*` in
      `mechanical/scripts/generate_eyes.py`, poi rigenerare

## 3. Stampa alloggio completo D50
- [ ] `Piatto_1_Piastra.3mf` — piastra (stampa lunga, da sola)
- [ ] `Piatto_2_pezzi.3mf` — bulbi, snodi, palpebre, tiranti, manovelle, LidBail, XHorn
      (supporti ad albero solo per i 2 snodi; brim sui 2 bulbi)
- [ ] Minuteria: filo armonico Ø1.5, 8 × M3×12 + dado, 1 × M3×25 + dado autobloccante + rondelle,
      viti M2 autofilettanti (16 mm per la LidBail), viti M4 + inserti per gli snodi
      (lunghezze dei tiranti in `mechanical/eyes/scaled/double_2servo_mg995/D50/info.txt`)

## 4. Montaggio
- [ ] Centrare i due MG995 a 90° (`servo_test.py --manual` → `90`) **prima** di montare squadrette e manovelle
- [ ] MG995 centrale + XHorn + 2 tiranti agli attacchi **interni** dei bulbi (bulbi dritti a 90°)
- [ ] MG995 palpebre + LidCrank_L; LidCrank_R sul perno M3; LidBail con 2 viti M2 per lato
- [ ] Tiranti fissi su/giù: bulbi in orizzontale, poi bloccare
- [ ] Muovere tutto a mano (servo staccati): niente punti duri, niente contatti

## 5. Prova movimento e codice
- [ ] Trovare le corse con `servo_test.py --manual`: sx/dx (min/centro/max) e palpebre (aperte/chiuse),
      annotare i µs
- [ ] Caricare `firmware/EyeNode_2servo` su un Nano (sx/dx su D3, palpebre su D5, alimentazione
      servo esterna) e tarare con i comandi seriali `c`, `l<us>`, `p<us>` → scrivere i valori in `CAL[]`
      di `config.h` (vedi `firmware/EyeNode_2servo/README.md`)
- [ ] Prova di movimento casuale per almeno 30 min: servo non troppo caldi, niente slittamenti
- [ ] Verificare che gli MG995 non tremino da fermi (sono economici: zona morta larga)

## 6. Scelta architettura (vedi `docs/architettura_controllo.md`)
- [ ] Prova sul banco: MG995 con 5 m di cavo 2 × 2.5 mm² per l'alimentazione (6 V) e 5 m di cavo
      twistato per il segnale; confrontare il tremolio con quello a cavo corto, anche con un altro
      motore acceso vicino
- [ ] Se va bene → Nano centrale + PCA9685 alla base (`CENTRAL_PCA9685 1`), altrimenti un Nano per testa
- [ ] Comprare un PCA9685 (meglio 2) se si sceglie la soluzione centrale

## 7. Poi: PCB
- [ ] Aggiornare requisiti e budget energetico: 2 MG995 per testa (picco ~5 A a 6 V) invece di 6–9 MG90S
- [ ] Secondo l'architettura scelta: EyeNode semplificata a 2 servo (+ mandibola) per ogni testa,
      oppure una scheda base unica (Nano + PCA9685 + fusibili per ramo + morsetti per i 4 colli)
- [ ] Decidere quanti MG995 comprare (ne servono 8 per 4 teste + ricambi; ne hai 5)
- [ ] Aggiornare `docs/lista_spesa.md`
