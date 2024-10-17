#ifndef I2C_LCD_h
#define I2C_LCD_h

#include <Wire.h>
#include <Arduino.h>

#define LCD_SCL0 digitalWrite(SCL, LOW);
#define LCD_SCL1 digitalWrite(SCL, HIGH);
#define LCD_SDA0 digitalWrite(SDA, LOW);
#define LCD_SDA1 digitalWrite(SDA, HIGH);


extern void initial_lcd(void);
extern void transfer(int data1);
extern void start_flag(void);
extern void stop_flag(void);
extern void disp_CGRAM(void);
extern void disp_char(int line,int column,char *dp);

#endif