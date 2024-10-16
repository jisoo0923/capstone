#include "SegmentLCD.h"

char dispnum[5]={0x00,0x00,0x00,0x00,0x00};

/*0,1,2,3,4,5,6,7,8,9,A,b,C,c,d,E,F,H,h,L,n,N,o,P,r,t,U,-, ,*/	  
const char num[]={0x7D,0x60,0x3E,0x7A,0x63,0x5B,0x5F,0x70,0x7F,0x7B,0x77,0x4F,0x1D,0x0E,0x6E,0x1F,0x17,0x67,0x47,0x0D,0x46,0x75,0x37,0x06,0x0F,0x6D,0x02,0x00,}; 
const char Table_Hello[]={0x00,0x67,0x1F,0x0D,0x0D,0x7D};			//HELLO
const char Table_Error[]={0x00,0x1F,0x77,0x77,0x7D,0x77};			//ERROR

//**********************************************************
//Sending data
//**********************************************************
void SendBit_1621(unsigned char sdat,unsigned char cnt) //data High cnt bits are written HT1621, the previous high 
{ 
	unsigned char i; 
	for(i=0;i<cnt;i++) 
	{ 
		LCD_WR0;
		delayMicroseconds(20); 
		if(sdat&0x80)
		{
			LCD_DATA1; 
		}
		else 
		{
			LCD_DATA0; 
		}
		delayMicroseconds(20); 
		LCD_WR1;
		delayMicroseconds(20); 
		sdat<<=1; 
	} 
	delayMicroseconds(20);  
}




//**********************************************************
//Send commands
//**********************************************************
void SendCmd_1621(unsigned char command)			//Send commands
{ 
	LCD_CS0; 
	SendBit_1621(0x80,4);    //Write flag code "100" and 9 the command
	SendBit_1621(command,8); //Did not have to make changes to the clock output commands such as, for programming convenience
	LCD_CS1;                     //Directly to the highest level of command write "0" 
} 

//**********************************************************
//Send commands and data
//**********************************************************
void Write_1621(unsigned char addr,unsigned char sdat) 
{ 
	addr<<=2; 
	LCD_CS0; 
	SendBit_1621(0xa0,3);     //Write flag code "101" 
	SendBit_1621(addr,6);     //Write addr high six 
	SendBit_1621(sdat,8);    //8-bit write data 
	LCD_CS1; 
}

//**********************************************************
//Some one to write a value
//**********************************************************
void Write_1621_data(unsigned char num,unsigned char sdat) 
{ 
	if(num < 6)
	{
		Write_1621(2*num,sdat);
	}
}

//**********************************************************
//Clear Display
//**********************************************************
void HT1621_all_off(unsigned char num) 
{ 
	unsigned char i; 
	unsigned char addr=0; 
	for(i=0;i<num;i++) 
	{ 
		Write_1621(addr,0x00); 
		addr+=2; 
	} 
}

//**********************************************************
//All lights
//**********************************************************
void HT1621_all_on(unsigned char num) 
{ 
	unsigned char i; 
	unsigned char addr=0; 
	for(i=0;i<num;i++) 
	{ 
		Write_1621(addr,0xff); 
		addr+=2; 
	} 
}

//**********************************************************
//All lights display the same number
//**********************************************************
void HT1621_all_on_num(unsigned char num,unsigned char xx) 
{ 
	unsigned char i; 
	unsigned char addr=0; 
	for(i=0;i<num;i++) 
	{ 
		Write_1621(addr,xx); 
		addr+=2; 
	} 
} 

//**********************************************************
//Initialization 1621
//**********************************************************
void Init_1621(void) 
{
	pinMode(LCD_DATA, OUTPUT); 
	pinMode(LCD_WR, OUTPUT); 
	pinMode(LCD_CS, OUTPUT); 
	LCDoff();
	SendCmd_1621(Sys_en);
	SendCmd_1621(RCosc);    
	SendCmd_1621(ComMode);  
	LCDon();
}

//**********************************************************
//LCD closed
//**********************************************************
void LCDoff(void) 
{  
	SendCmd_1621(LCD_off);  
} 

//**********************************************************
//LCD Open
//**********************************************************
void LCDon(void) 
{  
	SendCmd_1621(LCD_on);  
}


//**********************************************************
//The first two tests of digital strokes you for writing an array num
//**********************************************************
void Displaybihua(void) 
{ 	
	Write_1621(2,0x01);
	delay(350) ;
	Write_1621(2,0x02);
	delay(350) ;
	Write_1621(2,0x04);
	delay(350) ;
	Write_1621(2,0x08);
	delay(350) ;
	Write_1621(2,0X10);
	delay(350) ;
	Write_1621(2,0x20);
	delay(350) ;
	Write_1621(2,0x40);
	delay(350) ;
	Write_1621(2,0x80);
	delay(350) ;
}

//**********************************************************
//By 8-bit display characters + decimal point you
//**********************************************************	
void Displayall8(void)
{
	unsigned char i;
	HT1621_all_off(6);
	for(i=0;i<6;i++)
	{
		Write_1621(2*i,0xff);
		delay(50) ;
	}
}

////**********************************************************
////Display array data
////**********************************************************
//void Displaydata(long int t,int p,char bat1,char bat2,char bat3)//Screen display, bat1, bat2, bat3 the right side of the battery
//{
//	unsigned char i;
//	dispnum[5]=num[t/100000];
//	dispnum[4]=num[(t/10000)%10];
//	dispnum[3]=num[(t/1000)%10];
//	dispnum[2]=num[(t/100)%10];
//	dispnum[1]=num[(t/10)%10];
//	dispnum[0]=num[t%10];
//	switch(p)
//	{
//		case 1:
//		     sbi(dispnum[0], 7);
//		     break;
//		case 2:
//		     sbi(dispnum[1], 7);
//		     break;
//		case 3:
//		     sbi(dispnum[2], 7);
//		     break;
//		default:
//			cbi(dispnum[0], 7);
//			cbi(dispnum[1], 7);
//			cbi(dispnum[2], 7);
//		break;
//	}
//	if(bat1==1)  
//		sbi(dispnum[3], 7);
//	else
//		cbi(dispnum[3], 7);
//	if(bat2==1)  
//		sbi(dispnum[4], 7);
//	else
//		cbi(dispnum[4], 7);
//	if(bat3==1)  
//		sbi(dispnum[5], 7);
//	else
//		cbi(dispnum[5], 7);
//	
//	for(i=0;i<6;i++) 
//	{
//		Write_1621(i*2,dispnum[i]);
//	}
//}       



