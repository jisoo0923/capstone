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
    // 시리얼로부터 목표 무게 수신
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

    // 무게 측정
    unsigned long newWeight = Get_Weight();
    newWeight = (newWeight - Weight_Offset) * calibration_factor;

    if (newWeight != Weight) {  
        weightChanged = true;
        pumpStartTime = millis(); // 무게 변경 시 시간 초기화
    }

    Weight = newWeight;

    Serial.print("Weight: ");
    Serial.print(Weight);
    Serial.println(" g");

    // 목표 무게에 도달하지 않은 상태에서 펌프 제어
    if (!targetReached) {
        if (Weight < requiredWeight) {
            // 목표 무게에 도달하지 않은 경우 펌프 작동
            digitalWrite(in1, HIGH);
            digitalWrite(in2, LOW);
            pumpActivated = true; // 펌프 작동 상태 업데이트
        } else {
            // 목표 무게 도달 시 펌프 정지
            digitalWrite(in1, LOW);
            digitalWrite(in2, LOW);
            targetReached = true;  // 목표 무게 도달 상태 플래그 설정
            pumpActivated = false; // 펌프 작동 상태 플래그 해제
            Serial.println("Target weight reached. Pump stopped.");
        }
    } else {
        // 목표 무게 도달 상태에서 펌프 정지 유지
        if (pumpActivated) {
            digitalWrite(in1, LOW);
            digitalWrite(in2, LOW);
            pumpActivated = false; // 펌프 작동 상태 플래그 해제
            Serial.println("Pump is already stopped.");
        }
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
