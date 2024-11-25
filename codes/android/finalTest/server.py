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
CORS(app)  # CORS 설정 적용 (Cross-Origin Resource Sharing)

# YOLO 모델 로드 (사전 학습된 모델 파일 사용)
model = YOLO('best.pt')

# 전역 변수로 안드로이드 IP 주소 관리
ANDROID_IP = "192.168.229.43"

# 아두이노 시리얼 통신 설정 함수 (아두이노와 연결 시도 반복)
def setup_serial(port='COM9', baudrate=9600):
    # 아두이노와 시리얼 통신을 설정하는 함수.
    # 연결되지 않으면 5초 간격으로 재시도.
    while True:
        try:
            py_serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            print("시리얼 포트 연결 성공")
            return py_serial
        except Exception as e:
            print(f"시리얼 포트 연결 중 오류 발생: {e}")
            print("시리얼 포트에 연결되지 않았습니다. 5초 후 재시도합니다...")
            time.sleep(5)

# 아두이노 연결 설정
arduino = setup_serial()

# 서버 데이터 가져오기 함수
def fetch_data_from_server(server_url):
    # JSON 데이터를 서버에서 가져오는 함수.
    # :param server_url: JSON 데이터 서버 URL
    # :return: 서버에서 가져온 데이터 (딕셔너리 형태)
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # HTTP 에러 시 예외 발생
        return response.json()  # JSON 데이터를 파싱해서 반환
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

# 아두이노로 목표 무게 전송 함수
def send_target_weight(target_weight):
    # 아두이노로 목표 무게를 전송하는 함수.
    # :param target_weight: 목표 무게 (gram 단위)
    if arduino.is_open:
        weight_data = f"{target_weight}\n"  # 줄바꿈 문자를 포함하여 데이터 생성
        arduino.write(weight_data.encode())  # 시리얼 포트로 데이터 전송
        print(f"Sent target weight to Arduino: {target_weight}")
    else:
        print("Serial port is not open.")

# 안드로이드 알림 전송 함수
def notify_android(ip=None, message=""):
    # 안드로이드 앱으로 알림 메시지를 전송하는 함수.
    # :param ip: 안드로이드 기기의 IP 주소 (기본값: ANDROID_IP)
    # :param message: 전송할 알림 메시지
    target_ip = ip if ip else ANDROID_IP  # IP 주소 설정
    url = f"http://{target_ip}:8080/notify"  # 안드로이드에서 수신할 URL
    payload = {"message": message}

    for attempt in range(3):  # 최대 3회 재시도
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print("안드로이드에 알림 전송 성공:", response.json())
                return
            else:
                print(f"안드로이드 알림 전송 실패: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"안드로이드 알림 전송 중 오류 (시도 {attempt + 1}/3): {e}")

        if attempt < 2:  # 마지막 시도 전까지 대기
            time.sleep(2)  # 2초 대기
    else:
        print("안드로이드 알림 전송 실패: 모든 재시도 실패.")

# 목표 무게에 도달했을 때 호출
def on_target_weight_reached():
    # 목표 무게에 도달했을 때 호출되는 함수.
    # 안드로이드에 알림을 전송하고 통신 종료 메시지를 출력.
    print("목표 무게에 도달했습니다.")
    notify_android(message="물을 다 따랐습니다.")
    print("시리얼 통신 종료.")

# 목표 무게 실시간 확인 함수 (별도 스레드에서 동작)
def monitor_weight(target_weight):
    # 실시간으로 아두이노에서 현재 무게를 읽고 목표 무게와 비교하는 함수.
    # 목표 무게에 도달하면 알림을 전송하고 시리얼 통신 종료.
    # :param target_weight: 목표 무게
    try:
        target_weight = float(target_weight)  # 목표 무게를 숫자로 변환
    except ValueError:
        print("잘못된 목표 무게 데이터입니다. 숫자로 변환할 수 없습니다.")
        return

    try:
        while True:
            if arduino.in_waiting > 0:  # 시리얼 포트에서 데이터 대기 여부 확인
                weight_data = arduino.readline().decode().strip()
                print(f"Raw data received from Arduino: {weight_data}")

                try:
                    if weight_data.startswith("Weight: "):  # 무게 데이터 파싱
                        current_weight = float(weight_data.split("Weight: ")[1].split(" ")[0])
                        print(f"현재 무게: {current_weight} g")

                        if current_weight >= target_weight:  # 목표 무게 도달 여부 확인
                            print("목표 무게에 도달했습니다.")
                            notify_android(message="물을 다 따랐습니다.")
                            if arduino.is_open:
                                arduino.close()  # 시리얼 통신 종료
                                print("시리얼 통신 종료.")
                            break
                    else:
                        print("유효하지 않은 무게 데이터 수신")
                except ValueError:
                    print("유효하지 않은 무게 데이터 수신")
            time.sleep(0.1)  # 데이터를 0.1초마다 확인
    except Exception as e:
        print(f"모니터링 중 오류 발생: {e}")

# 안드로이드 IP 설정 엔드포인트
@app.route('/set_android_ip', methods=['POST'])
def set_android_ip():
    # 안드로이드 IP 주소를 설정하는 엔드포인트.
    # 안드로이드 기기에서 IP 주소를 전달받아 설정.
    global ANDROID_IP
    try:
        data = request.json
        ANDROID_IP = data.get("ip", ANDROID_IP)  # 전달받은 IP 주소 설정
        print(f"안드로이드 IP 주소가 {ANDROID_IP}로 설정되었습니다.")
        return jsonify({"status": "success", "ip": ANDROID_IP})
    except Exception as e:
        print(f"IP 설정 중 오류 발생: {e}")
        return jsonify({"status": "fail", "message": str(e)})

# 안드로이드에서 이미지 업로드 처리 엔드포인트
@app.route('/', methods=['POST'])
def upload():
    # 안드로이드에서 이미지 업로드 시 호출되는 엔드포인트.
    # 이미지를 YOLO 모델로 분석하고 결과에 따라 제품 정보를 반환.
    try:
        file = request.files['image']  # 이미지 파일 수신
        if file:
            image = Image.open(io.BytesIO(file.read()))  # 이미지를 메모리에서 읽기
            image.save("received_image.jpg")  # 저장
            print("이미지 저장 완료")

            results = model(image)  # YOLO 모델로 분석
            labels = []

            for result in results:  # YOLO 결과에서 라벨 추출
                for box in result.boxes:
                    label = result.names[int(box.cls[0])]
                    labels.append(label)

            if labels:
                label_to_search = labels[0]  # 첫 번째 라벨 사용
                print(f"찾은 라벨: {label_to_search}")

                server_url = "http://52.78.208.162/getjson.php"  # 제품 정보 서버 URL
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

                        volume = product_info.get('volume', None)  # 목표 부피 확인
                        if volume and volume != 'unknown':
                            send_target_weight(volume)  # 목표 무게 전송
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

# Flask 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
