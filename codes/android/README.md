### 1. strings.xml
```xml
<resources>
    <string name="app_name">Ramen Recognition Project</string>
    <string name="captured_image">Captured Image</string>
    <string name="capture_button_text">Capture Image</string>
    <string name="label_product_name">제품명: </string>
    <string name="label_maker">제조사: </string>
    <string name="label_recipe">조리법: </string>
</resources>
```

### 2. build.gradle
- dependencies에 추가
  
```
implementation("com.google.code.gson:gson:2.8.8")
implementation("com.squareup.okhttp3:okhttp:4.9.1")
```

### 3. 서버 코드 수정
- 카메라 이미지 전송 수정 : 앱에서 찍은 사진을 서버로 전송받아 처리하므로 카메라 프레임 추출 부분 제거하고, 서버로부터 이미지 받아서 YOLO 모델에 전달하도록 수정
    - 수정 전
        ```py
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("카메라를 열 수 없습니다.")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("캠에서 사진을 가져올 수 없습니다.")
                break
        ```
    - 수정 후
        ```py
        # 서버에서 이미지 가져오기 함수
        def get_image_from_server():
        try:
            response = requests.get("http://서버주소/이미지엔드포인트")
            response.raise_for_status()
            nparr = np.frombuffer(response.content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except requests.exceptions.RequestException as e:
            print(f"이미지 요청 중 오류 발생: {e}")
            return None
        ```
- 물 감지하고 모터와의 통신기능 추가 **(추가 수정필요)** : 물의 적정 무게를 조절하기 위해 아두이노와 시리얼 통신을 하여 펌프의 모터와 상호작용하도록 수정
    - 수정 전
        ```py
        def monitor_weight(py_serial, target_weight):
        while True:
            if py_serial.in_waiting > 0:
                weight_data = py_serial.readline().decode().strip()
                try:
                    current_weight = float(weight_data)
                    print(f"현재 무게: {current_weight} g")

                    if current_weight >= target_weight:
                        print("목표 무게에 도달했습니다.")
                        reach_weight()
                        break
                except ValueError:
                    print("유효하지 않은 무게 데이터 수신")
            time.sleep(0.1)
        ```
  - 수정 후
    ```py
        def monitor_weight_with_pump(py_serial, target_weight):
            motor_on = False
            while True:
                if py_serial.in_waiting > 0:
                    weight_data = py_serial.readline().decode().strip()
                    try:        
                        current_weight = float(weight_data)
                        print(f"현재 무게: {current_weight} g")

                        if current_weight < target_weight and not motor_on:
                            # 모터를 켜서 물을 추가
                            py_serial.write(b'MOTOR_ON\n')
                            motor_on = True
                            print("모터를 켰습니다.")
                
                        elif current_weight >= target_weight and motor_on:
                            # 모터를 꺼서 물 공급 중지
                            py_serial.write(b'MOTOR_OFF\n')
                            motor_on = False
                            reach_weight()
                            print("목표 무게에 도달하여 모터를 껐습니다.")
                            break
                    except ValueError:
                        print("유효하지 않은 무게 데이터 수신")
            time.sleep(0.1)
    ```

- TTS 음성 안내 내용 변경
    - 수정 전
        ```py
        def speak_product_info(product, speed=200):
            engine = pyttsx3.init()
            engine.setProperty('rate', speed)  # 음성 속도 조절
            if product is not None:  # product가 None이 아닐 때
                text = f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}"
            else:
                text = "해당 라벨의 제품을 찾을 수 없습니다."  # 오류 메시지
            engine.say(text)
            engine.runAndWait()
        ```
  - 수정 후
    ```py
        def speak_product_info(product, speed=200):
            engine = pyttsx3.init()
            engine.setProperty('rate', speed)  # 음성 속도 조절
            if product is not None:  # product가 None이 아닐 때
                text = (f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}. "f"적정량의 물을 부을 준비를 해주세요.")
            else:
                text = "해당 라벨의 제품을 찾을 수 없습니다."  # 오류 메시지
            engine.say(text)
            engine.runAndWait()
    ```
