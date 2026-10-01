#pragma once
#include "Arduino.h"
struct EEPROMT { uint8_t m[64]={0}; template<class T> void get(int a,T&v){memcpy(&v,m+a,sizeof v);} template<class T> void put(int a,const T&v){memcpy(m+a,&v,sizeof v);} };
extern EEPROMT EEPROM;
