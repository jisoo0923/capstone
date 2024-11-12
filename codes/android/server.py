import cv2
from ultralytics import YOLO
import requests
import pyttsx3
import json
import serial
import time
import winsound

# YOLO 모델 불러오기 함수
def load_yolo_model(model_path):
    return YOLO(model_path)

# 데이터베이스에서 가져온 JSON을 담을 리스트
db_list = []

# DBData 클래스 정의
class DBData:
    def __init__(self):
        self.label = None
        self.name = None
        self.maker = None
        self.recipe = None

    def set_member_label(self, label):
        self.label = label

    def set_member_name(self, name):
        self.name = name

    def set_member_maker(self, maker):
        self.maker = maker

    def set_member_recipe(self, recipe):
        self.recipe = recipe

# 서버에서 데이터를 가져오는 함수
def fetch_data_from_server(server_url):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

# JSON 데이터를 파싱하는 함수
def parse_json_data(json_string):
    try:
        data = json.loads(json_string)
        if 'test' in data and isinstance(data['test'], list):
            for item in data['test']:
                if all(key in item for key in ['rabel', 'name', 'maker', 'recipe']):
                    dbData = DBData()
                    dbData.set_member_label(item.get('rabel', 'unknown'))
                    dbData.set_member_name(item.get('name', 'unknown'))
                    dbData.set_member_maker(item.get('maker', 'unknown'))
                    dbData.set_member_recipe(item.get('recipe', 'unknown'))
                    db_list.append(dbData)
            print(f"데이터 파싱 성공: {len(db_list)}개 항목 추가됨")
        else:
            print("'test' 키가 없거나 배열이 아닙니다.")
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

# 라벨을 기준으로 데이터베이스에서 제품을 찾는 함수
def find_product_by_label(label):
    if not db_list:
        print("데이터베이스가 비어 있습니다.")
        return None
    for product in db_list:
        if product.label == label:
            return product
    return None

# 제품 정보를 음성으로 알려주는 함수
def speak_product_info(product, speed=200):
    engine = pyttsx3.init()
    engine.setProperty('rate', speed)  # 음성 속도 조절
    if product is not None:  # product가 None이 아닐 때
        text = f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}"
    else:
        text = "해당 라벨의 제품을 찾을 수 없습니다."  # 오류 메시지
    engine.say(text)
    engine.runAndWait()

# 시리얼 통신 초기화
def setup_serial(port='COM9', baudrate=9600):
    try:
        py_serial = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        print("시리얼 포트 연결 성공")
        return py_serial
    except Exception as e:
        print(f"시리얼 포트 연결 중 오류 발생: {e}")
        return None

# 목표 무게 도달하면 음성 안내 함수
def reach_weight():
    winsound.Beep(1000, 500)  # 1000 Hz, 0.5초 길이의 삐 소리
    engine = pyttsx3.init()
    engine.say("목표 무게에 도달했습니다.")
    engine.runAndWait()

# 목표 무게 실시간 확인 함수
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

# YOLO 모델을 이용해 컵라면 인식 및 제품 정보 출력 함수
def detect_and_announce(server_url, model_path, serial_port):
    model = load_yolo_model(model_path)
    json_data = fetch_data_from_server(server_url)
    if json_data:
        parse_json_data(json_data)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("캠에서 사진을 가져올 수 없습니다.")
            break

        results = model(frame)
        object_detected = False

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0]
                label = int(box.cls[0])
                if conf < 0.90:
                    continue

                class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
                product = find_product_by_label(class_name)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # 빨간색으로 바운딩 박스
                cv2.putText(frame, f'Label: {class_name}, Conf: {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                speak_product_info(product)
                object_detected = True
                break

            if object_detected:
                break

        if object_detected:
            print("객체를 인식했습니다.")
            weight = input("목표 무게를 입력하세요 (g): ")
            try:
                target_weight = float(weight)
                monitor_weight(serial_port, target_weight)
            except ValueError:
                print("유효한 무게를 입력하세요.")
            break

        cv2.imshow('컵라면 인식', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# 클래스명 리스트
class_names = ['buldak', 'buldak4Cheese', 'buldakCarbo', 'buldakSoup',
               'buldakSoup2', 'carboSoup', 'carboSoup2', 'cheeseSoup',
               'cheeseSoup2', 'jinHot', 'jinHotSoup', 'jinMild', 'jinMildSoup',
               'kaguri', 'kaguriSoup', 'kimchi', 'kimchiSoup', 'kimchiSoup2',
               'king', 'kingSoup', 'kingSoup2', 'ojingeo', 'ojingeoSoup', 'sesame',
               'sesameSoup1', 'sesameSoup2', 'sesameSoup3', 'shin', 'shinSoup',
               'wang', 'wangSoup', 'wangSoup2']

# 메인 함수
if __name__ == "__main__":
    server_url = "http://43.203.182.200/getjson.php"
    model_path = 'best.pt'
    serial_port = setup_serial(port='COM9', baudrate=9600)
    detect_and_announce(server_url, model_path, serial_port)