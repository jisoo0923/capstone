from flask import Flask, request, jsonify
from PIL import Image
import io
import os

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # 이미지 파일을 열고 저장합니다.
        image = Image.open(image_file.stream)
        save_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image.save(save_path)
        print(f"이미지 저장 완료: {save_path}")
        
        # 이미지 처리 후 결과 반환하는 예제
        result = {"message": "Image received successfully", "filename": image_file.filename}
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
