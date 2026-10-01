// Simulatore PC: compila EyeNode_random.ino con finti Arduino/Servo/EEPROM.
// Uso: sim.exe <indirizzo DIP> <seme di prova> <secondi>  -> CSV su stdout (us dei 6 servo, umore)
#include "Arduino.h"
#include "Servo.h"
#include "EEPROM.h"
uint32_t simMs=0; uint8_t simAddr=0; uint64_t rngState=88172645463325252ull; SerialT Serial; EEPROMT EEPROM;
#include "EyeNode_random.ino"
#include <stdlib.h>
int main(int argc,char**argv){
  simAddr=atoi(argv[1]); rngState ^= (uint64_t)atoll(argv[2])*0x9E3779B97F4A7C15ull;
  uint32_t dur = atoi(argv[3])*1000u;
  setup();
  printf("t,a_lr,a_ud,a_lid,b_lr,b_ud,b_lid,mood\n");
  uint32_t last=0;
  while(simMs<dur){ loop(); simMs++;
    if(simMs-last>=20){ last=simMs; printf("%u,%d,%d,%d,%d,%d,%d,%d\n",simMs,servo[0][0].us,servo[0][1].us,servo[0][2].us,servo[1][0].us,servo[1][1].us,servo[1][2].us,mood);} }
}
