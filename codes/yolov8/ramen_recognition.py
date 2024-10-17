import cv2
import serial
import time
from ultralytics import YOLO
import requests
import json
import pyttsx3

# 시리얼 통신 설정 (아두이노 포트와 맞춰야 함)
ser = serial.Serial('COM6', 9600, timeout=1)  # 아두이노 연결 포트
time.sleep(2)  # 아두이노와 통신 대기 시간

# YOLO 모델 로드
model = YOLO('best.pt')

# 컵라면 종류별로 필요한 물의 양 설정
water_requirements = {
    'buldak': 550,
    'buldakCarbo': 500,
    'jinHotSoup': 520
}

def fetch_data_from_server(server_url):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

def manual_input():
    print("컵라면 종류를 수동으로 입력하세요:")
    print(list(water_requirements.keys()))  # 선택 가능한 종류 출력
    label = input("라벨을 입력하세요: ")
    return label

def main():
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            print("캠에서 사진을 가져올 수 없습니다.")
            label = manual_input()  # 수동 입력으로 라벨 받기
            break

        # YOLO 모델로 캠 프레임 추론
        results = model(frame)

        if len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            label = int(box.cls[0])
            class_names = ['buldak', 'buldakCarbo', 'jinHotSoup']
            class_name = class_names[label] if label < len(class_names) else 'Unknown'
            print(f"{class_name} 인식됨")

            if class_name in water_requirements:
                needed_water = water_requirements[class_name]
            else:
                print("컵라면 종류를 수동으로 입력하세요:")
                class_name = manual_input()
                needed_water = water_requirements.get(class_name, 500)
            break
        else:
            print("컵라면 종류를 인식하지 못했습니다.")
            label = manual_input()  # 수동 입력으로 라벨 받기
            break

    # 필요 물의 양을 아두이노로 전송
    ser.write(f"{needed_water}\n".encode('utf-8'))
    print(f"{needed_water}g의 물의 양을 아두이노로 전송했습니다.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
