# Idra di Guerra

Teste animatroniche del carro **"Idra di Guerra"** (Carnevale di Viareggio): occhi stampati in 3D
mossi da servo con movimento autonomo e casuale.

## Struttura
```
mechanical/eyes/eyemech_D85/   occhi in uso (bulbo Ø85): Testa_1 … Testa_4 = piatti di stampa di ogni testa, pezzi/ = un STL per pezzo
mechanical/mandibola/          supporto regolabile del servo mandibola (DS3225)
firmware/EyeD85_random/        movimento casuale degli occhi D85 (ESP8266 ESP-12F + PCA9685)
firmware/EyeD85_zero/          tutti i servo a 90° + taratura via seriale (da usare per montare le squadrette)
firmware/EyeNode_random/       movimento casuale per la scheda EyeNode (Arduino Nano)
hardware/kicad/EyeNode/        schematico, PCB e gerber della scheda EyeNode
docs/img/                      disegni: cablaggio, giunti, palpebre, mandibola, viste della scheda
```

## Ramo `archivio`
Il resto del progetto è sul ramo **`archivio`**: modelli originali (EyeMech ε3.2, MorganManly),
idra_version, gambe, script Python che generano STL / piatti / PCB, simulatore del firmware,
firmware EyeNode_2servo e servo_test, documentazione testuale (requisiti, elettronica, lista spesa, TODO).
```bash
git checkout archivio
```

## Regola chiave per gli occhi
Il bulbo è ingrandito (Ø85), ma la **sede del servo resta in scala 1:1**
(i servomotori non cambiano dimensione).

## Licenza dei modelli
Gli occhi derivano da **EyeMech ε3.2** di Will Cogley e da **Animatronic Eyes** di MorganManly,
entrambi **CC BY-NC-SA 4.0**: anche i pezzi derivati qui sono CC BY-NC-SA 4.0 (attribuzione, uso non
commerciale, stessa licenza).
