from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import requests
import json
from ultralytics import YOLO

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
    app.run(host='0.0.0.0', port=50505)
