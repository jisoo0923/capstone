from flask import Flask, request, jsonify
from PIL import Image
import io
from ultralytics import YOLO

# Flask 앱 초기화
app = Flask(__name__)

# YOLO 모델 로드
model = YOLO('best.pt')

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
                    labels.append(result.names[int(box.cls[0])])

            # 인식된 라벨을 JSON 형태로 반환
            response = {"status": "success", "labels": labels}
            print(f"응답 데이터: {response}")
            return jsonify(response)
        else:
            print("이미지가 업로드되지 않았습니다.")
            return {"status": "fail", "message": "No image uploaded."}
    except Exception as e:
        print(f"오류 발생: {e}")
        return {"status": "fail", "message": "서버 처리 중 오류 발생"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50505)
