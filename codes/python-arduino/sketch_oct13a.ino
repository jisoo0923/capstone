// 목표무게 한번 도달하면 바로 워터펌프 멈추는 코드

// Include Library
#include <I2C_LCD.h>
#include <HX24.h>
#include <SegmentLCD.h>

// define pins for L298N motor driver
#define in1 7  // L298N IN1 핀
#define in2 6  // L298N IN2 핀

// Global variables
unsigned long Weight = 0;
unsigned long Weight_Offset = 0;  // 영점 조정값
unsigned long requiredWeight = 0; // 목표 무게
float calibration_factor = 1.1;   // 보정 상수
bool pumpActivated = false;       // 워터펌프 작동 여부 플래그
bool targetReached = false;       // 목표 무게 도달 여부 플래그
unsigned long pumpStartTime = 0;  // 워터펌프 작동 시작 시간
unsigned long pumpDelay = 2000;   // 워터펌프 지연 시간 (2초)
bool weightChanged = false;       // 무게가 변경되었는지 플래그
char msg[16] = {0x01};

void setup() {
    Serial.begin(9600);
    delay(100);

    pinMode(in1, OUTPUT);
    pinMode(in2, OUTPUT);
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);

    Init_HX24();  
    Init_1621();  
    initial_lcd();  

    for (unsigned char i = 0; i < 6; i++) Write_1621_data(5 - i, Table_Hello[i]);
    Serial.println("Setup completed.");

    Weight_Offset = Get_Weight();
    Serial.print("Weight Offset: ");
    Serial.println(Weight_Offset);
}

void loop() {
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');  // 줄바꿈 문자까지 읽기
        requiredWeight = input.toInt();  // 정수로 변환
        
        if (requiredWeight > 0) {
            Serial.print("Target weight set to: ");
            Serial.println(requiredWeight);
            pumpActivated = false;  // 새로운 목표 무게 설정 시 펌프 초기화
            targetReached = false;  // 목표 무게 도달 여부 초기화
        } else {
            Serial.println("Invalid target weight received.");
        }
    }

    // 무게 측정 및 제어 로직
    unsigned long newWeight = Get_Weight();
    newWeight = (newWeight - Weight_Offset) * calibration_factor;

    if (newWeight != Weight) {  
        weightChanged = true;
        pumpStartTime = millis();
    }

    Weight = newWeight;

    Serial.print("Weight: ");
    Serial.print(Weight);
    Serial.println(" g");

    if (!targetReached && weightChanged && millis() - pumpStartTime >= pumpDelay) {
        if (Weight < requiredWeight) {
            digitalWrite(in1, HIGH);
            digitalWrite(in2, LOW);
        } else {
            digitalWrite(in1, LOW);
            digitalWrite(in2, LOW);
            targetReached = true;  // 목표 무게 도달
            Serial.println("Target weight reached. Pump stopped.");
        }
        pumpActivated = true;
        weightChanged = false;
    }

    if (targetReached) {
        digitalWrite(in1, LOW);
        digitalWrite(in2, LOW);  // 목표 무게 도달 후 펌프 정지 유지
    }

    // Segment LCD에 현재 무게 출력
    Write_1621_data(5, 0x00);
    Write_1621_data(4, 0x00);
    Write_1621_data(3, num[Weight / 1000]);
    Write_1621_data(2, num[Weight % 1000 / 100] | 0x80);
    Write_1621_data(1, num[Weight % 100 / 10]);
    Write_1621_data(0, num[Weight % 10]);

    sprintf(msg, "%12d g  ", Weight);
    disp_char(2, 1, msg);

    delay(500); // 0.5초마다 무게 측정
}
