### **작업의 주요 흐름과 개선 사항(241117)**

1. **문제 인식**:
   - 처음에는 저울의 무게 변화와 관계없이 목표 무게를 수신하면 즉시 워터펌프가 작동하는 문제가 있었습니다.
   - 또한 딜레이를 줄 경우에도 목표 무게에 도달했음에도 펌프가 계속 작동하는 상황이 발생했습니다.

2. **해결 방법 및 개선**:
   - **무게 변화 후 1초 지연** 로직을 추가하여, 무게 변화가 감지된 후 일정 시간(1초)이 지나야 펌프가 작동하도록 개선했습니다.
   - **목표 무게 도달 시 펌프 즉시 정지**: 목표 무게에 도달하면 펌프가 멈추고, 다시 목표 무게 설정을 대기하도록 로직을 보완했습니다.
   - **알림 기능 추가**: 목표 무게에 도달했을 때 안드로이드 앱에 **"물을 다 따랐습니다"**라는 알림을 보내고, 이를 **TTS(Text-to-Speech)**로 음성 출력하도록 설정했습니다.

---

### **최종 코드 설명**

#### 1. **아두이노 코드**

**기능 추가**:
- **무게 변화 후 1초 지연** 로직을 적용하여, 무게 변화가 감지된 후 1초 동안 기다린 후 펌프가 작동하도록 설정했습니다.
- **목표 무게 도달 시 펌프 즉시 정지** 및 서버로 상태 메시지 전송.

```cpp
#include <I2C_LCD.h>
#include <HX24.h>
#include <SegmentLCD.h>

#define in1 7  // L298N IN1 핀
#define in2 6  // L298N IN2 핀

unsigned long Weight = 0;
unsigned long Weight_Offset = 0;  
unsigned long requiredWeight = 0; 
float calibration_factor = 1.1;   
bool pumpActivated = false;       
bool targetReached = false;       
unsigned long weightChangeTime = 0; 
unsigned long pumpDelay = 1000;   
bool weightChanged = false;       
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
        String input = Serial.readStringUntil('\n');  
        unsigned long newRequiredWeight = input.toInt();  

        if (newRequiredWeight > 0) {
            requiredWeight = newRequiredWeight;
            Serial.print("Target weight set to: ");
            Serial.println(requiredWeight);
            targetReached = false;
            pumpActivated = false;
            weightChanged = false; 
        } else {
            Serial.println("Invalid target weight received.");
        }
    }

    unsigned long newWeight = Get_Weight();
    newWeight = (newWeight - Weight_Offset) * calibration_factor;

    if (newWeight != Weight) {  
        weightChanged = true;
        weightChangeTime = millis();  
    }

    Weight = newWeight;

    Serial.print("Weight: ");
    Serial.print(Weight);
    Serial.println(" g");

    if (!targetReached) {
        if (weightChanged && millis() - weightChangeTime >= pumpDelay) {
            if (Weight < requiredWeight) {
                digitalWrite(in1, HIGH);
                digitalWrite(in2, LOW);  
                pumpActivated = true;
                Serial.println("Pump activated.");
            } else {
                digitalWrite(in1, LOW);
                digitalWrite(in2, LOW);
                targetReached = true;    
                pumpActivated = false;
                Serial.println("Target weight reached. Pump stopped.");
            }
        }
    }

    if (Weight >= requiredWeight) {
        if (pumpActivated) {
            digitalWrite(in1, LOW);
            digitalWrite(in2, LOW);
            pumpActivated = false;
            Serial.println("Pump stopped due to weight exceeded.");
        }
        targetReached = true;  
    }

    Write_1621_data(5, 0x00);
    Write_1621_data(4, 0x00);
    Write_1621_data(3, num[Weight / 1000]);
    Write_1621_data(2, num[Weight % 1000 / 100] | 0x80);
    Write_1621_data(1, num[Weight % 100 / 10]);
    Write_1621_data(0, num[Weight % 10]);

    sprintf(msg, "%12d g  ", Weight);
    disp_char(2, 1, msg);

    delay(500); 
}
```

---

#### 2. **Flask 서버 코드**

**기능 추가**:
- **목표 무게 도달 시 안드로이드로 알림 전송**: `notify_android` 함수를 통해 알림을 보내도록 설정했습니다.
- **무게 모니터링**: `monitor_weight` 함수에서 목표 무게 도달 여부를 확인하고, 알림 전송.

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import requests
import serial
import threading
import time
from ultralytics import YOLO

app = Flask(__name__)
CORS(app)

model = YOLO('best.pt')

def setup_serial(port='COM9', baudrate=9600):
    while True:
        try:
            py_serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            print("Serial connected")
            return py_serial
        except Exception as e:
            print(f"Serial connection error: {e}. Retrying...")
            time.sleep(5)

arduino = setup_serial()

def notify_android(ip, message):
    url = f"http://{ip}:8080/notify"
    payload = {"message": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Notification sent to Android:", response.json())
        else:
            print(f"Failed to send notification: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Notification error: {e}")

def monitor_weight(target_weight):
    while True:
        if arduino.in_waiting > 0:
            weight_data = arduino.readline().decode().strip()
            print(f"Arduino data: {weight_data}")
            if weight_data.startswith("Weight: "):
                current_weight = float(weight_data.split("Weight: ")[1])
                if current_weight >= target_weight:
                    notify_android("192.168.4.4", "물을 다 따랐습니다.")
                    break
        time.sleep(0.1)

@app.route('/', methods=['POST'])
def upload():
    file = request.files['image']
    image = Image.open(io.BytesIO(file.read()))
    image.save("received_image.jpg")
    results = model(image)
    label = results[0].names[0] 
    volume = 500  # Sample volume
    send_target_weight(volume)
    threading.Thread(target=monitor_weight, args=(volume,)).start()
    return jsonify({"status": "success"})
```

---

#### 3. **안드로이드 코드**

**기능 추가**:
- **NanoHTTPD 서버**를 사용하여 Flask 서버로부터 알림을 수신하고, **TTS**로 메시지를 음성 출력.

```java
public class HTTPServer extends NanoHTTPD {
    public HTTPServer(int port) {
        super(port);
    }

    @Override
    public Response serve(IHTTPSession session) {
        if (Method.POST.equals(session.getMethod()) && "/notify".equals(session.getUri())) {
            try {
                Map<String, String> files = new HashMap<>();
                session.parseBody(files);
                String json = files.get("postData");

                ServerMessage message = new Gson().fromJson(json, ServerMessage.class);

                runOnUiThread(() -> {
                    textToSpeech.speak(message.getMessage(), TextToSpeech.QUEUE_FLUSH, null, null);
                });
                return newFixedLengthResponse(Response.Status.OK, "application/json", "{\"status\": \"success\"}");
            } catch (Exception e) {
                return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, "application/json", "{\"status\": \"error\"}");
            }
        }
        return newFixedLengthResponse(Response.Status.NOT_FOUND, "application/json", "{\"status\": \"not_found\"}");
    }
}
``` 

---

### **최종 기능 요약**
- **아두이노**: 무게 변화 후 2초 지연, 목표 무게 도달 시 즉시 펌프 정지.
- **Flask 서버**: YOLO 모델로 컵라면 인식 및 무게 설정, 목표 무게 도달 시 안드로이드로 알림.
- **안드로이드 앱**: 사진 업로드, 제품 정보 음성 안내, 목표 무게 도달 알림 수신 및 TTS 안내.



### **작업의 주요 흐름과 개선 사항(2411124)**

## 추가된 기능

### 1. 권한 요청 통합
- 앱 실행 시 필요한 모든 권한을 한 번에 요청.
- 권한: 카메라, 음성 녹음.
- 변경 후: 모든 권한을 한 번에 요청하도록 수정.
   - 수정된 메서드: checkRequiredPermissions
   - 요청할 권한을 배열로 정의하고, 필요한 권한만 필터링하여 한 번에 요청.

---

### 2. 음성 인식
- 음성 명령어로 라면 정보를 요청.
  - 명령어 예시:
    - "조리법" → 조리법 안내.
    - "제조사" → 제조사 안내.
    - 추가 클래스 및 메서드:
      - SpeechRecognizer 초기화 (initSpeechRecognizer)
      - 음성 명령어 처리 (handleVoiceCommand)
      - 음성 인식 결과를 반영해 TTS로 정보를 읽어주는 기능.

---

### 3. TTS 속도 조절
- 변경 후: TTS 속도를 사용자가 느리게, 빠르게, 초기화할 수 있는 UI 및 기능 추가.
   - 추가 버튼:
      - 느리게 (ttsCtlSlow)
      - 빠르게 (ttsCtlFast)
      - 다시 읽기 (ttsCtlRestart)
   - 관련 메서드: adjustTtsSpeed

---

### 4. 진동 피드백
- 버튼 클릭 시 진동 제공.
   - 관련 코드:
      - Vibrator 객체 추가 및 진동 메서드 (vibrate) 구현.

---
  
### 5. 동적 IP 관리(=클라이언트 IP주소 하드코딩 개선)
- 변경 전: Android 기기의 IP 주소가 고정되어 있었음.
- 변경 후: Android 기기 실행 시 동적으로 IP 주소를 서버로 전달하는 기능 추가.
   - 앱 실행 시 Android의 로컬 IP를 서버에 자동으로 전달.
   - 서버(PC)는 전달받은 IP로 알림을 보냄.
   - 추가 메서드:
      - configureDynamicIp
      - getLocalIpAddress
      - sendIpToServer

---

### 6. Flask 서버 개선(=서버 IP주소 하드코딩 개선)
- IP 설정 API 추가:
   - Android 기기의 동적 IP를 서버에서 관리 가능하도록 /set_android_ip 엔드포인트 추가.
   - Android가 IP를 POST 요청으로 전달하면 서버가 이를 저장.
- 알림 전송 안정화:
   - Android 알림 전송 로직에 최대 3회 재시도와 타임아웃 설정 추가 (notify_android).

---



## UI 변화와 추가된 기능 정리

---

### 변경 전 UI (기존 코드 기준)

#### **기능**
- **캡처 버튼**: 사진 촬영 및 서버 업로드.
- **텍스트뷰**: 제품명, 제조사, 조리법 정보를 표시.
- **이미지뷰**: 촬영된 이미지를 화면에 표시.(실제로는 보이지 않고 라면인식을 위해서 처리되는 항목)

#### **부족한 점**
- TTS 속도 조절 버튼 없음.
- 음성 명령을 위한 UI 없음.
- 터치 시 피드백(진동) 없음.

---

### 변경 후 UI

#### **추가된 UI 요소 및 UI 동작 개선**
1. **TTS 제어 버튼**:
   -  0.25 단위로 속도조절
   - `ttsCtlSlow`: TTS 속도를 느리게 조정.(하한선 0.5)
   - `ttsCtlFast`: TTS 속도를 빠르게 조정.(상한선 2.0)
   - `ttsCtlRestart`: 제품 정보를 다시 읽기.
2. **음성 인식 버튼**:
   - `listenButton`: 음성 명령어를 입력받기 위한 버튼.
      - 명령어로 제품명(명령어: 이름, 제품명), 제조사(명령어: 제조사, 브랜드), 조리법(명령어: 조리법, 레시피) 정보를 요청.
3. **텍스트뷰 표시 개선**:
   - `textViewName`, `textViewMaker`, `textViewRecipe`는 데이터를 받아올 때까지 숨겨져 있다가, 데이터 수신 후 자동 표시.
   - 가독성을 높이기 위해 정보의 구분을 명확히 표시.

---



