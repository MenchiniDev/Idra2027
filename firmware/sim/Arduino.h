#pragma once
#include <stdint.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <algorithm>
typedef uint8_t byte;
#define F(x) x
#define HEX 16
#define LOW 0
#define HIGH 1
#define OUTPUT 1
#define INPUT_PULLUP 2
enum { A0=14,A1,A2,A3,A4,A5,A6,A7 };
using std::max; using std::min;
extern uint32_t simMs; extern uint8_t simAddr; extern uint64_t rngState;
inline uint32_t millis(){return simMs;}
inline uint32_t micros(){return simMs*1000u+ (uint32_t)(rngState>>40)%1000;}
inline void delay(uint32_t d){simMs+=d;}
inline void delayMicroseconds(uint32_t){}
inline void pinMode(uint8_t,uint8_t){}
inline int digitalRead(uint8_t p){ int bit=p-A0; return (simAddr>>bit)&1 ? LOW:HIGH; }
inline void digitalWrite(uint8_t,int){}
inline uint32_t xs(){ rngState^=rngState<<13; rngState^=rngState>>7; rngState^=rngState<<17; return (uint32_t)(rngState>>16); }
inline int analogRead(uint8_t p){ return p==A7 ? 612 + (int)(xs()%5) : 300 + (int)(xs()%40); }
static uint32_t arSeed=1;
inline void randomSeed(uint32_t s){ arSeed=s?s:1; }
inline long ar(){ arSeed = arSeed*1103515245u+12345u; return (arSeed>>1)&0x7fffffff; }
inline long random(long a,long b){ if(b<=a) return a; return a + ar()%(b-a); }
inline long random(long b){ return random(0,b); }
struct SerialT { void begin(long){} int available(){return 0;} int read(){return -1;}
 template<class T> void print(T){ } template<class T> void print(T,int){} template<class T> void println(T){} template<class T> void println(T,int){} void println(){} };
extern SerialT Serial;
