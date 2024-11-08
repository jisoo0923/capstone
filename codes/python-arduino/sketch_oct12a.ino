// Include Library
#include <I2C_LCD.h>
#include <HX24.h>
#include <SegmentLCD.h>

// define pin 
#define relay 2 

// Global variable
unsigned long Weight = 0;
unsigned long Weight_Offset = 0;  // 영점 조정값
char msg[16] = {0x01};

// 보정 상수 초기화
float calibration_factor = 1.15;

void setup() {
    Serial.begin(9600);
    delay(100);  // 시리얼 통신 안정화를 위한 짧은 대기

    // 핀 모드 설정
    pinMode(relay, OUTPUT);
    digitalWrite(relay, LOW);

    // Initialize libraries
    Init_HX24();  // 로드셀 라이브러리 초기화
    Init_1621();  // Segment LCD 라이브러리 초기화
    initial_lcd();  // 1602 I2C LCD 초기화

    // LCD 초기 메시지
    for (unsigned char i = 0; i < 6; i++) Write_1621_data(5 - i, Table_Hello[i]);  // "HELLO" 표시
    Serial.println("Setup completed.");

    // 영점 조정 (로드셀에 아무것도 올리지 않은 상태에서)
    Weight_Offset = Get_Weight();
    Serial.print("Weight Offset: ");
    Serial.println(Weight_Offset);
}

void loop() {
    // 현재 무게 측정 및 영점 조정과 보정 상수 적용
    Weight = Get_Weight();
    Weight = (Weight - Weight_Offset) * calibration_factor; // 오프셋 및 보정 상수 적용

    // 무게 출력 (Error 메시지 제거)
    Serial.print("Weight: ");
    Serial.print(Weight);
    Serial.println(" g");

    // Relay work
    if (Weight >= 100) {
        digitalWrite(relay, HIGH);
    } else {
        digitalWrite(relay, LOW);
    }

    // Segment LCD에 현재 무게 출력
    Write_1621_data(5, 0x00);  // Not Displayed
    Write_1621_data(4, 0x00);
    Write_1621_data(3, num[Weight / 1000]);
    Write_1621_data(2, num[Weight % 1000 / 100] | 0x80);  // 소수점 추가
    Write_1621_data(1, num[Weight % 100 / 10]);
    Write_1621_data(0, num[Weight % 10]);

    sprintf(msg, "%12d g  ", Weight);
    disp_char(2, 1, msg);

    delay(500);  // 0.5초마다 무게 측정
}
