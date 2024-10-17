// Include Library
#include <I2C_LCD.h>
#include <HX24.h>
#include <SegmentLCD.h>

// define pin 
#define relay 2 
#define buzzer 3  // 부저 핀 추가 (신호 출력용)

// Global variable
unsigned long Weight = 0;
unsigned long requiredWeight = 0;  // 파이썬에서 받은 목표 무게
unsigned long Weight_Set=0;    //저울 영점 조절용 직전 무게

bool waterPoured = false;  // 물을 따랐는지 여부
bool Weight_Flag=false;    //저울 영점 조절

char msg[16] = {0x01};

// 보정 상수 초기화
float calibration_factor = 2.6;  // 필요에 따라 조정. 초기값 1.15. 1.1818

void setup() {
    Serial.begin(9600);
    
    // 핀 모드 설정
    pinMode(relay, OUTPUT);
    pinMode(buzzer, OUTPUT);  // 부저 핀 추가
    digitalWrite(relay, LOW);  // 초기 상태에서 릴레이 끔
    digitalWrite(buzzer, LOW);  // 초기 상태에서 부저 끔

    // Initialize libraries
    Init_HX24();  // 로드셀 라이브러리 초기화
    Init_1621();  // Segment LCD 라이브러리 초기화
    initial_lcd();  // 1602 I2C LCD 초기화

    // LCD 초기 메시지
    for (unsigned char i = 0; i < 6; i++) Write_1621_data(5 - i, Table_Hello[i]);  // "HELLO" 표시
    Serial.println("Setup completed.");
}

void loop() {
    // 시리얼로부터 목표 무게 수신
    if (Serial.available() > 0) {
        requiredWeight = Serial.parseInt();  // 파이썬에서 보낸 목표 무게 수신
        waterPoured = false;  // 물을 따르기 시작하기 전으로 초기화
        Serial.print("Received target weight: ");
        Serial.println(requiredWeight);
    }

    // 현재 무게 측정 및 보정
    Weight = Get_Weight();
    Weight = Weight * calibration_factor;  // 보정 상수 적용

    //저울 영점 조절
    if (!Weight_Flag){
      Weight_Set = Weight;
      Weight_Flag=true;
    }
    Weight -= Weight_Set;

    if (Weight<0)
      Weight=0;
    else if (Weight>5000){
      Flag_Error=1;
      Weight=0;
    }

    // 현재 무게 출력
    Serial.print("Current Weight: ");
    Serial.print(Weight);
    Serial.println(" g");


    // 세그먼트 LCD에 현재 무게 출력
    if (Flag_Error == 0) {
        Write_1621_data(5, 0x00);  // Not Displayed
        Write_1621_data(4, 0x00);				
        Write_1621_data(3, num[Weight / 1000]);				
        Write_1621_data(2, num[Weight % 1000 / 100] | 0x80);  // 소수점 추가
        Write_1621_data(1, num[Weight % 100 / 10]);
        Write_1621_data(0, num[Weight % 10]);

        sprintf(msg, "%12d g  ", Weight);
        disp_char(2,1,msg);

      // 목표 무게에 도달하지 않으면 물 붓기
      if (Weight < requiredWeight && !waterPoured) {
          digitalWrite(relay, HIGH);  // 릴레이 켜서 물 붓기 시작
          Serial.println("Pouring water...");
      }
      // 목표 무게에 도달하면 물 멈추기 및 신호 출력
      else if (Weight > requiredWeight && !waterPoured) {
          digitalWrite(relay, LOW);  // 물 멈추기
          waterPoured = true;  // 물 붓기 완료 상태

          // 세그먼트 LCD에 "DONE" 출력
          disp_char(1,1,"  D O N E  ");
          Serial.println("Water pouring done.");
      }
    }

    else {
        // 에러 상황 시 에러 메시지 출력
        for (unsigned char i = 0; i < 6; i++) {
            Write_1621_data(5 - i, Table_Error[i]);  // "ERROR" 표시
        }
        disp_char(1, 1, "  E  R  R  O  R ");
    }

    delay(3000);  // 10초마다 무게 측정. 소음으로 수정
}