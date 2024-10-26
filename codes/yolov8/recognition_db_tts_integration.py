import cv2
from ultralytics import YOLO
import requests
import pyttsx3
import json
from db_tts import DBData

# 1. 모델 로딩
def load_model(model_path):
    return YOLO(model_path)

# 2. 카메라 초기화
def initialize_camera():
    return cv2.VideoCapture(0)

# 3. 서버에서 JSON 데이터 가져오기
def fetch_data_from_server(server_url):
    response = requests.get(server_url)
    if response.status_code == 200:
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            print("JSON 파싱 오류 발생.")
            return None
    else:
        print("서버에서 데이터를 가져오지 못했습니다.")
        return None

# 4. JSON 데이터를 파싱하여 제품 데이터 리스트에 저장
def parse_json_data(json_data):
    db_list = []
    if isinstance(json_data, list):
        for item in json_data:
            dbData = DBData()
            dbData.set_member_label(item.get('label', 'unknown'))
            dbData.set_member_name(item.get('name', 'unknown'))
            dbData.set_member_maker(item.get('maker', 'unknown'))
            dbData.set_member_recipe(item.get('recipe', 'unknown'))
            db_list.append(dbData)
    return db_list

# 5. 라벨에 맞는 데이터 찾기
def find_product_by_label(db_list, label):
    if not db_list:
        print("데이터베이스가 비어 있습니다.")
        return None
    for product in db_list:
        if product.label == label:
            return product
    return None

# 6. 객체 감지
def detect_objects(model, frame):
    return model(frame)

# 7. 박스와 라벨 그리기
def draw_boxes_and_labels(frame, results, class_names):
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = box.conf[0]
            label = int(box.cls[0])
            class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # 빨간색으로 변경
            cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

# 8. 제품 정보를 음성으로 안내
def speak_product_info(product, speed=200):
    engine = pyttsx3.init()
    engine.setProperty('rate', speed)
    if product is not None:
        text = f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}"
    else:
        text = "해당 라벨의 제품을 찾을 수 없습니다."
    engine.say(text)
    engine.runAndWait()

# 9. 카메라 통한 실시간 객체 감지 실행
def run_detection(server_url, model_path, class_names):
    model = load_model(model_path)
    cap = initialize_camera()
    json_data = fetch_data_from_server(server_url)
    db_list = parse_json_data(json_data)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("캠에서 사진을 가져올 수 없습니다.")
            break

        results = detect_objects(model, frame)
        draw_boxes_and_labels(frame, results, class_names)

        for result in results:
            for box in result.boxes:
                label = int(box.cls[0])
                class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
                product = find_product_by_label(db_list, class_name)
                speak_product_info(product)

        cv2.imshow('컵라면 인식', frame)

        if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:  # 27: 'ESC'키의 아스키 코드
            break


    cap.release()
    cv2.destroyAllWindows()

# 메인 함수 호출
if __name__ == "__main__":
    server_url = "http://43.203.182.200/getjson.php"
    model_path = 'best.pt'
    class_names = [
        'buldak', 'buldak4Cheese', 'buldakCarbo', 'buldakSoup',
        'buldakSoup2', 'carboSoup', 'carboSoup2', 'cheeseSoup',
        'cheeseSoup2', 'jinHot', 'jinHotSoup', 'jinMild', 'jinMildSoup',
        'kaguri', 'kaguriSoup', 'kimchi', 'kimchiSoup', 'kimchiSoup2',
        'king', 'kingSoup', 'kingSoup2', 'ojingeo', 'ojingeoSoup', 'sesame',
        'sesameSoup1', 'sesameSoup2', 'sesameSoup3', 'shin', 'shinSoup',
        'wang', 'wangSoup', 'wangSoup2'
    ]

    run_detection(server_url, model_path, class_names)