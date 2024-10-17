#include "I2C_LCD.h"

void initial_lcd(void){
  start_flag(); 
  transfer(0x78);
  transfer(0x00);
  transfer(0x38); // function set
  transfer(0x0c); // display on/off
  transfer(0x01); // clear display
  transfer(0x06);
  stop_flag(); 
}

void transfer(int data1){
  int i;
  for(i=0;i<8;i++)
  {
    LCD_SCL0;
    if(data1&0x80){ LCD_SDA1;}
    else LCD_SDA0;
    LCD_SCL1;
    LCD_SCL0;
    data1=data1<<1;
  }
  LCD_SDA0;
  LCD_SCL1;
  LCD_SCL0;
}

void start_flag(void){
	LCD_SCL1;
	LCD_SDA1;
	LCD_SDA0;
}

void stop_flag(void){
	LCD_SCL1;
	LCD_SDA0;
	LCD_SDA1;
}

void disp_CGRAM(void){
  int i;
  start_flag();
  transfer(0x78); 
  transfer(0x80); 
  transfer(0x80); 
  transfer(0x40); 
  for(i=0;i<16;i++)
  {
    transfer(0x01);
  }
  stop_flag();
  start_flag();
  transfer(0x78); 
  transfer(0x80); 
  transfer(0xc0); 
  transfer(0x40); 
  for(i=0;i<16;i++)
  {
    transfer(0x01);
  }
  stop_flag();
}

void disp_char(int line,int column,char *dp){
	int i;
  start_flag();
  transfer(0x78); 
  transfer(0x80); 
  transfer(0x80+(line-1)*0x40+(column-1)); 
  transfer(0x40); 
  for(i=0;i<16;i++)
  {
    transfer(*dp);
    dp=dp+1;
  }
  stop_flag();
}