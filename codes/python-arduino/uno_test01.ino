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
