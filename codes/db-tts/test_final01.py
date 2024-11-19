from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import requests
import json
import serial
import threading
import time
from ultralytics import YOLO

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)  # CORS 설정 적용

# YOLO 모델 로드
model = YOLO('best.pt')

# 아두이노 시리얼 통신 설정 함수 (아두이노와 연결 시도 반복)
def setup_serial(port='COM9', baudrate=9600):
    while True:
        try:
            py_serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            print("시리얼 포트 연결 성공")
            return py_serial
        except Exception as e:
            print(f"시리얼 포트 연결 중 오류 발생: {e}")
            print("시리얼 포트에 연결되지 않았습니다. 5초 후 재시도합니다...")
            time.sleep(5)  # 5초 대기 후 다시 시도

# 아두이노 연결 설정
arduino = setup_serial()

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

# 목표 무게 실시간 확인 함수 (별도 스레드에서 동작)
def monitor_weight(target_weight):
    try:
        target_weight = float(target_weight)
    except ValueError:
        print("잘못된 목표 무게 데이터입니다. 숫자로 변환할 수 없습니다.")
        return

    try:
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

                            # 목표 무게 도달 후 안드로이드에 알림 전송
                            notify_android()

                            # 시리얼 통신 종료
                            if arduino.is_open:
                                arduino.close()
                                print("시리얼 통신 종료.")
                            break
                    else:
                        print("유효하지 않은 무게 데이터 수신")
                except ValueError:
                    print("유효하지 않은 무게 데이터 수신")
            time.sleep(0.1)  # 데이터를 0.1초마다 확인
    except Exception as e:
        print(f"모니터링 중 오류 발생: {e}")

# 안드로이드에 "물을 다 따랐습니다" 알림 전송 함수
def notify_android():
    print("안드로이드에 알림: 물을 다 따랐습니다.")
    # Firebase 등의 알림 시스템을 사용한다면 여기에 그 코드 추가

@app.route('/', methods=['POST'])
def upload():
    try:
        # 이미지 파일 수신
        file = request.files['image']
        if file:
            image = Image.open(io.BytesIO(file.read()))
            image.save("received_image.jpg")
            print("이미지 저장 완료")

            results = model(image)
            labels = []

            for result in results:
                for box in result.boxes:
                    label = result.names[int(box.cls[0])]
                    labels.append(label)

            if labels:
                label_to_search = labels[0]
                print(f"찾은 라벨: {label_to_search}")

                server_url = "http://52.78.208.162/getjson.php"
                data = fetch_data_from_server(server_url)

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

                        volume = product_info.get('volume', None)
                        if volume and volume != 'unknown':
                            send_target_weight(volume)
                            threading.Thread(target=monitor_weight, args=(volume,)).start()
                    else:
                        response = {"status": "fail", "message": "제품 정보를 찾을 수 없습니다."}
                else:
                    response = {"status": "fail", "message": "JSON 데이터 서버에서 데이터를 가져오는 데 실패했습니다."}
            else:
                response = {"status": "fail", "message": "라벨을 인식하지 못했습니다."}

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
