#line 1 "C:\\Users\\loren\\Desktop\\Idra2027\\firmware\\EyeD85_zero\\README.md"
# EyeD85_zero — tutti i servo a 90° + taratura

Primo sketch da caricare sugli occhi D85 (ESP8266 + PCA9685, canali 4 = X, 6 = Y, 10/11 = palpebre
sx/dx): all'accensione porta i 4 servo a 90° (occhi dritti, palpebre chiuse) per montare le squadrette,
poi dal Monitor seriale (115200) si muove un servo alla volta e il comando `p` stampa le righe di
taratura da incollare in `EyeD85_random/config.h`.

Collegamenti, Arduino IDE e procedura completa: [`../EyeD85_random/README.md`](../EyeD85_random/README.md).
