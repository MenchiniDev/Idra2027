#pragma once
#include "Arduino.h"
struct Servo { int us=1500; bool att=false; uint8_t pin=0;
 void attach(uint8_t p,int,int){pin=p;att=true;} void detach(){att=false;} bool attached(){return att;}
 void writeMicroseconds(int v){ us = std::max(544,std::min(2400,v)); } };
