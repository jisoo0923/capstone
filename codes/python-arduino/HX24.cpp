#include "hx24.h"

unsigned long HX24_Buffer = 0;
unsigned long Weight_M = 0,Weight_S = 0;
bool Flag_Error = 0;

//****************************************************
//Initialization HX24
//****************************************************
void Init_HX24()
{
	pinMode(HX24_SCK, OUTPUT);	
	pinMode(HX24_DT, INPUT);
}


//****************************************************
//Get fur weight
//****************************************************
void Get_M()
{
	HX24_Buffer = HX24_Read();
	Weight_M = HX24_Buffer/100;		
} 

//****************************************************
//Weigh
//****************************************************
unsigned int Get_Weight()
{
	HX24_Buffer = HX24_Read();
	HX24_Buffer = HX24_Buffer/100;

	if(HX24_Buffer > Weight_M)			
	{
		Weight_S = HX24_Buffer;
		Weight_S = Weight_S - Weight_M;				//Get real AD sampling value.
	
		Weight_S = (unsigned int)((float)Weight_S/8.25+0.05); 	
			//Calculate the actual weight of the real thing
			//Because different sensor characteristic curves are different, therefore, each sensor needs to be corrected here is the divisor 7.35
			//When they find out the test weight is too large, increase the value
			//If the test out of the weight is too small, decrease the changed value.
			//This value is typically between 7.0-8.0. May be due to the different sensors.
			//+0.05 Percentile to rounding
	}

	// 오류 조건 확인 및 플래그 설정
   	if (Weight_S > 3000 || HX24_Buffer < Weight_M - 30) {
        Flag_Error = 1;
        // 아래 줄을 주석 처리하여 시리얼 출력에서 "Error" 메시지를 제거합니다.
        // Serial.print("Error");
	}
	else
	{
		Flag_Error = 0;	
	}	
	return Weight_S;
}

//****************************************************
//Read HX24
//****************************************************
unsigned long HX24_Read(void)	//Gain 128
{
	unsigned long count; 
	unsigned char i;
	bool Flag = 0;

	digitalWrite(HX24_DT, HIGH);
	delayMicroseconds(1);

	digitalWrite(HX24_SCK, LOW);
	delayMicroseconds(1);

  	count=0; 
  	while(digitalRead(HX24_DT)); 
  	for(i=0;i<24;i++)
	{ 
	  	digitalWrite(HX24_SCK, HIGH); 
		delayMicroseconds(1);
	  	count=count<<1; 
		digitalWrite(HX24_SCK, LOW); 
		delayMicroseconds(1);
	  	if(digitalRead(HX24_DT))
			count++; 
	} 
 	digitalWrite(HX24_SCK, HIGH); 
	delayMicroseconds(1);
	digitalWrite(HX24_SCK, LOW); 
	delayMicroseconds(1);
	count ^= 0x800000;
	return(count);
}
