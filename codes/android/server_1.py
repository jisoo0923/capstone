from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import requests
import json
from ultralytics import YOLO
import serial
import time

# Flask 앱 초기화
app = Flask(__name__)
CORS(app)  # CORS 설정 적용

# YOLO 모델 로드
model = YOLO('best.pt')

# 서버 데이터 가져오기 함수
def fetch_data_from_server(server_url):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.json()  # JSON 데이터를 반환
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

print("서버가 시작되었습니다...")

# 시리얼 포트 초기화
serial_port = None

def setup_serial(port='COM9', baudrate=9600):
    """시리얼 통신 초기화"""
    try:
        global serial_port
        serial_port = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        print("시리얼 포트 연결 성공")
    except Exception as e:
        print(f"시리얼 포트 연결 중 오류 발생: {e}")
        serial_port = None

def send_target_weight(target_weight):
    """아두이노로 목표 무게 전송"""
    if serial_port and serial_port.is_open:
        weight_data = f"{target_weight}\n"  # 줄바꿈 문자 포함
        serial_port.write(weight_data.encode())  # 데이터 전송
        print(f"Sent target weight: {target_weight}")
    else:
        print("Serial port is not open or available.")

def receive_weight():
    """아두이노에서 현재 무게 데이터 수신"""
    if serial_port and serial_port.in_waiting > 0:
        weight_data = serial_port.readline().decode().strip()
        print(f"Raw data received: {weight_data}")
        return weight_data
    return None

@app.route('/current_weight', methods=['GET'])
def get_current_weight():
    """현재 무게 반환"""
    try:
        weight = receive_weight()
        if weight:
            return jsonify({"status": "success", "current_weight": weight})
        else:
            return jsonify({"status": "fail", "message": "No weight data available."}), 204
    except Exception as e:
        return jsonify({"status": "fail", "message": f"Error retrieving weight: {str(e)}"}), 500

@app.route('/', methods=['POST'])
def upload():
    try:
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

            if labels:
                label_to_search = labels[0]
                print(f"찾은 라벨: {label_to_search}")

                # 외부 JSON 데이터 서버에서 정보 가져오기
                server_url = "http://43.203.182.200/getjson.php"
                data = fetch_data_from_server(server_url)

                if data and 'test' in data and isinstance(data['test'], list):
                    product_info = next((item for item in data['test'] if item['rabel'] == label_to_search), None)

                    if product_info:
                        target_weight = 100  # 디폴트 목표 무게 설정
                        send_target_weight(target_weight)  # 목표 무게 전송

                        response = {
                            "status": "success",
                            "label": label_to_search,
                            "product_info": {
                                "name": product_info.get('name', 'unknown'),
                                "maker": product_info.get('maker', 'unknown'),
                                "recipe": product_info.get('recipe', 'unknown')
                            },
                            "target_weight": target_weight
                        }
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

            return jsonify(response)
        else:
            return jsonify({"status": "fail", "message": "No image uploaded."}), 400
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({"status": "fail", "message": "서버 처리 중 오류 발생"}), 500

if __name__ == '__main__':
    setup_serial(port='COM9', baudrate=9600)  # 시리얼 포트 설정
    app.run(host='0.0.0.0', port=5000)
