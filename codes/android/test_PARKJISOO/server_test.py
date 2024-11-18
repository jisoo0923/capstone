from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import requests
import json
import serial
import threading
import time
import pyttsx3  # Text-to-speech for server-side notifications
from ultralytics import YOLO

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)  # CORS 설정 적용

# YOLO 모델 로드
model = YOLO('best.pt')

# 시리얼 통신 설정 (아두이노와 연결)
try:
    # 시리얼 포트 설정 (OS에 따라 경로 수정 필요)
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # 리눅스/맥용 예시
    # Windows에서는 다음과 같이 설정할 수 있음:
    # arduino = serial.Serial('COM3', 9600, timeout=1)
    print("시리얼 포트 연결 성공")
except AttributeError as e:
    print(f"시리얼 포트 연결 오류 발생: {e}")
except Exception as e:
    print(f"예기치 못한 오류 발생: {e}")


# 서버 데이터 가져오기 함수
def fetch_data_from_server(server_url):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.json()  # JSON 데이터를 반환
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

# 아두이노로 목표 무게 전송 함수
def send_target_weight(target_weight):
    if arduino.is_open:
        weight_data = f"{target_weight}\n"  # 줄바꿈 문자를 포함하여 전송
        arduino.write(weight_data.encode())  # 시리얼로 데이터 전송
        print(f"Sent target weight to Arduino: {target_weight}")
    else:
        print("Serial port is not open.")

# 목표 무게 도달 시 음성 안내 함수
def reach_weight():
    engine = pyttsx3.init()
    engine.say("목표 무게에 도달했습니다.")
    engine.runAndWait()

# 목표 무게 실시간 확인 함수 (별도 스레드에서 동작)
def monitor_weight(target_weight):
    while True:
        if arduino.in_waiting > 0:
            weight_data = arduino.readline().decode().strip()
            print(f"Raw data received from Arduino: {weight_data}")

            try:
                if weight_data.startswith("Weight: "):
                    current_weight = float(weight_data.split("Weight: ")[1].split(" ")[0])
                    print(f"현재 무게: {current_weight} g")

                    if current_weight >= target_weight:
                        print("목표 무게에 도달했습니다.")
                        reach_weight()
                        
                        # 목표 무게 도달 후 안드로이드에 알림 전송
                        notify_android()
                        break
                else:
                    print("유효하지 않은 무게 데이터 수신")
            except ValueError:
                print("유효하지 않은 무게 데이터 수신")
        time.sleep(0.1)  # 데이터를 0.1초마다 확인

# 안드로이드에 "물을 다 따랐습니다" 알림 전송 함수
def notify_android():
    # 여기서는 단순히 서버 로그로 출력하지만, 필요에 따라 안드로이드 앱으로 HTTP 요청 등을 보낼 수 있음
    print("안드로이드에 알림: 물을 다 따랐습니다.")
    # 만약 Firebase 등의 알림 시스템을 사용한다면 여기에 그 코드 추가

print("서버가 시작되었습니다...")

@app.route('/', methods=['POST'])
def upload():
    try:
        # 이미지 파일 수신
        file = request.files['image']
        if file:
            # 이미지를 열어서 저장
            image = Image.open(io.BytesIO(file.read()))
            image.save("received_image.jpg")
            print("이미지 저장 완료")

            # YOLO 모델을 이용해 이미지 분석
            results = model(image)
            labels = []

            for result in results:
                for box in result.boxes:
                    label = result.names[int(box.cls[0])]
                    labels.append(label)

            # 라벨 중 첫 번째 것을 기준으로 제품 정보 조회
            if labels:
                label_to_search = labels[0]
                print(f"찾은 라벨: {label_to_search}")

                # 외부 JSON 데이터 서버에서 정보 가져오기
                server_url = "http://43.203.182.200/getjson.php"
                data = fetch_data_from_server(server_url)

                # JSON 데이터에서 라벨에 맞는 제품 정보 찾기
                if data and 'test' in data and isinstance(data['test'], list):
                    product_info = next((item for item in data['test'] if item['rabel'] == label_to_search), None)

                    if product_info:
                        response = {
                            "status": "success",
                            "label": label_to_search,
                            "product_info": {
                                "name": product_info.get('name', 'unknown'),
                                "maker": product_info.get('maker', 'unknown'),
                                "recipe": product_info.get('recipe', 'unknown')
                            }
                        }

                        # 아두이노로 목표 물의 양(volume) 전송
                        volume = product_info.get('volume', None)
                        if volume and volume != 'unknown':
                            send_target_weight(volume)
                            # 목표 무게 모니터링을 별도의 스레드에서 실행
                            threading.Thread(target=monitor_weight, args=(volume,)).start()

                    else:
                        response = {
                            "status": "fail",
                            "message": f"라벨 '{label_to_search}'에 대한 제품 정보를 찾을 수 없습니다."
                        }
                else:
                    response = {
                        "status": "fail",
                        "message": "JSON 데이터 서버에서 데이터를 가져오는 데 실패했습니다."
                    }
            else:
                response = {
                    "status": "fail",
                    "message": "라벨을 인식하지 못했습니다."
                }

            # 응답 반환
            print(f"응답 데이터: {response}")
            return jsonify(response)
        else:
            print("이미지가 업로드되지 않았습니다.")
            return {"status": "fail", "message": "No image uploaded."}, 400
    except Exception as e:
        print(f"오류 발생: {e}")
        return {"status": "fail", "message": "서버 처리 중 오류 발생"}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
