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
unsigned long weightChangeTime = 0; // 무게 변화 감지 시간
unsigned long pumpDelay = 1000;   // 워터펌프 지연 시간 (1초)
bool weightChanged = false;       // 무게 변화 여부 플래그
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
    // 목표 무게 수신
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');  // 줄바꿈 문자까지 읽기
        unsigned long newRequiredWeight = input.toInt();  // 정수로 변환

        if (newRequiredWeight > 0) {
            requiredWeight = newRequiredWeight;
            Serial.print("Target weight set to: ");
            Serial.println(requiredWeight);
            targetReached = false; // 새로운 목표 무게 설정 시 초기화
            pumpActivated = false;
            weightChanged = false; // 새로운 목표 무게 설정 후 초기화
        } else {
            Serial.println("Invalid target weight received.");
        }
    }

    // 무게 측정
    unsigned long newWeight = Get_Weight();
    newWeight = (newWeight - Weight_Offset) * calibration_factor;

    if (newWeight != Weight) {  
        weightChanged = true;  // 무게 변화 감지
        weightChangeTime = millis();  // 무게 변화 시 시간 기록
    }

    Weight = newWeight;

    Serial.print("Weight: ");
    Serial.print(Weight);
    Serial.println(" g");

    // 목표 무게에 도달하지 않은 상태에서만 동작
    if (!targetReached) {
        if (weightChanged && millis() - weightChangeTime >= pumpDelay) {
            if (Weight < requiredWeight) {
                digitalWrite(in1, HIGH);
                digitalWrite(in2, LOW);  // 펌프 작동
                pumpActivated = true;
                Serial.println("Pump activated.");
            } else {
                // 목표 무게 도달 시 즉시 펌프 정지
                digitalWrite(in1, LOW);
                digitalWrite(in2, LOW);
                targetReached = true;    // 목표 무게 도달
                pumpActivated = false;
                Serial.println("Target weight reached. Pump stopped.");
            }
        }
    }

    // 목표 무게에 도달하거나 초과한 경우 펌프를 지속적으로 정지
    if (Weight >= requiredWeight) {
        if (pumpActivated) {
            digitalWrite(in1, LOW);
            digitalWrite(in2, LOW);  // 펌프 정지
            pumpActivated = false;
            Serial.println("Target weight reached.");  // 목표 무게 도달 메시지 전송
            Serial.println("Pump stopped due to weight exceeded.");
        }
        targetReached = true;  // 목표 무게 초과시에도 정지 유지
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
