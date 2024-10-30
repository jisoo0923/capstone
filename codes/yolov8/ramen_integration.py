import cv2
from ultralytics import YOLO
import requests
import pyttsx3
import json
import serial
import time

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

# 모델 로딩
def load_model(model_path):
    return YOLO(model_path)

# 내장 카메라 초기화
def initialize_camera():
    return cv2.VideoCapture(0)

# 서버에서 JSON 데이터 가져오기
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

# JSON 데이터 파싱해서 리스트에 저장
def parse_json_data(json_data):
    db_list = []
    if isinstance(json_data, list):
        for item in json_data:
            dbData = DBData()
            dbData.set_member_label(item.get('label', None))
            dbData.set_member_name(item.get('name', None))
            dbData.set_member_maker(item.get('maker', None))
            dbData.set_member_recipe(item.get('recipe', None))
            db_list.append(dbData)
    return db_list

# 라벨에 맞는 데이터 찾기
def find_product_by_label(db_list, label):
    if not db_list:
        print("데이터베이스가 비어 있습니다.")
        return None
    for product in db_list:
        if product.label == label:
            return product
    return None

# 객체 감지
def detect_objects(model, frame):
    return model(frame)

# 바운딩 박스와 라벨 그리기
def draw_boxes_and_labels(frame, results, class_names):
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = box.conf[0]
            label = int(box.cls[0])
            class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # 빨간색으로 변경
            cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

# 제품 정보를 음성으로 안내
def speak_product_info(product, speed=200):
    engine = pyttsx3.init()
    engine.setProperty('rate', speed)
    if product is not None:
        text = f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}"
    else:
        text = "해당 제품을 찾을 수 없습니다."
    engine.say(text)
    engine.runAndWait()

# 아두이노 시리얼 통신 초기화
def initialize_serial(port='/dev/ttyUSB0', baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        return ser
    except serial.SerialException:
        print("아두이노와의 시리얼 연결에 실패했습니다. 아두이노가 연결되어 있지 않습니다.")
        return None

# 아두이노로 신호 보내기
def send_signal_to_arduino(ser, signal):
    if ser is not None:
        ser.write(signal.encode())

# 아두이노의 응답 읽기
def read_from_arduino(ser):
    if ser is not None and ser.in_waiting > 0:
        data = ser.readline().decode().strip()
        print(f"아두이노 응답: {data}")

# 실시간 객체 감지 실행
def run_detection(server_url, model_path, class_names, serial_port='/dev/ttyUSB0', baudrate=9600):
    model = load_model(model_path)
    cap = initialize_camera()
    ser = initialize_serial(serial_port, baudrate)
    json_data = fetch_data_from_server(server_url)
    db_list = parse_json_data(json_data)
    object_detected = False
    CONFIDENCE_THRESHOLD = 0.8  # 신뢰도 임계값 설정

    while cap.isOpened():
        time.sleep(0.5)  # 인식 속도를 줄이기 위해 0.5초 대기
        ret, frame = cap.read()
        if not ret:
            print("캠에서 사진을 가져올 수 없습니다.")
            break

        results = detect_objects(model, frame)
        draw_boxes_and_labels(frame, results, class_names)

        for result in results:
            for box in result.boxes:
                label = int(box.cls[0])
                conf = box.conf[0]  # 신뢰도 값 가져와서 정의

                # 신뢰도가 임계값 이상인 경우에만 제품 정보 출력
                if conf >= CONFIDENCE_THRESHOLD:
                    class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
                    product = find_product_by_label(db_list, class_name)

                    # 제품 정보를 음성으로 출력
                    speak_product_info(product)

                    # 아두이노 신호 전송
                    send_signal_to_arduino(ser, '1')

                    # 아두이노 응답 읽기
                    read_from_arduino(ser)

                    # 객체가 인식되었으므로 프레임을 이미지로 저장
                    output_filename = f'detected_{class_name}_{conf:.2f}.jpg'
                    cv2.imwrite(output_filename, frame)
                    print(f"인식된 객체 이미지 저장: {output_filename}")

                    object_detected = True  # 객체가 감지되었음을 표시

                    # 객체를 감지한 후 반복문 종료
                    break

            if object_detected:
                break

        # 객체 감지 후 종료
        if object_detected:
            print("객체를 인식했습니다. 프로그램을 종료합니다.")
            break

        # 결과 프레임 화면에 표시
        cv2.imshow('컵라면 인식', frame)

        # 'q' 키 또는 'ESC' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
            break

    cap.release()
    if ser is not None:
        ser.close()
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
