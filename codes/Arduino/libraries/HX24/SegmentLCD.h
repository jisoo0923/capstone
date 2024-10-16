#ifndef __SEGMENTLCD__H__
#define __SEGMENTLCD__H__

#include <Arduino.h>

//Definition of HT1621 command 
#define  ComMode    0x52  //4COM,1/3bias  1000    010 1001  0  
#define  RCosc      0x30  //Internal RC oscillator (power-on default)1000 0011 0000 
#define  LCD_on     0x06  //Open the LCD bias generator1000     0000 0 11 0 
#define  LCD_off    0x04  //Turn off LCD display 
#define  Sys_en     0x02  //System oscillator open 1000   0000 0010 
#define  CTRl_cmd   0x80  //Write Control Commands 
#define  Data_cmd   0xa0  //Write Data command 

//Set variable register function
#define sbi(x, y)  (x |= (1 << y))   /*Y bit in the first register is x's*/
#define cbi(x, y)  (x &= ~(1 <<y ))  /*The first bit register is cleared x of y*/  

//IO port definitions
#define LCD_DATA 10
#define LCD_WR 11
#define LCD_CS 12


//Define data port port HT1621 
#define LCD_DATA1    digitalWrite(LCD_DATA,HIGH) 
#define LCD_DATA0    digitalWrite(LCD_DATA,LOW) 
#define LCD_WR1      digitalWrite(LCD_WR,HIGH)  
#define LCD_WR0      digitalWrite(LCD_WR,LOW)   
#define LCD_CS1      digitalWrite(LCD_CS,HIGH)  
#define LCD_CS0      digitalWrite(LCD_CS,LOW)

//Function declaration
extern void SendBit_1621(unsigned char sdat,unsigned char cnt); //data High cnt bits are written HT1621, the previous high
extern void SendCmd_1621(unsigned char command);			//Send commands
extern void Write_1621(unsigned char addr,unsigned char sdat);
extern void HT1621_all_off(unsigned char num);
extern void HT1621_all_on(unsigned char num);
extern void HT1621_all_on_num(unsigned char num,unsigned char xx);
extern void LCDoff(void);
extern void LCDon(void);
extern void Displaybihua(void);
extern void Init_1621(void);
extern void Displayall8(void);
//extern void Displaydata(long int t,int p,char bat1,char bat2,char bat3);	//Screen display, bat1, bat2, bat3 the right side of the battery
extern void Write_1621_data(unsigned char num,unsigned char sdat) ;



extern char dispnum[5];
extern const char num[]; 
extern const char Table_Hello[];
extern const char Table_Error[];

#endif