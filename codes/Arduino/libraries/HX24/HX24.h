#ifndef __HX24__H__
#define __HX24__H__

#include <Arduino.h>

#define HX24_SCK 5
#define HX24_DT 4

extern void Init_HX24();
extern unsigned long HX24_Read(void);
extern unsigned int Get_Weight();
extern void Get_M();
extern bool Flag_Error;

#endif