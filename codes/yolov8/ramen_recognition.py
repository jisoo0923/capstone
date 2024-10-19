import cv2
from ultralytics import YOLO

# 모델 로딩 함수
def load_model(model_path):
    return YOLO(model_path)

# 카메라 초기화 함수
def initialize_camera():
    return cv2.VideoCapture(0)

# 객체 감지 함수
def detect_objects(model, frame):
    return model(frame)

# 박스와 라벨 그리기 함수
def draw_boxes_and_labels(frame, results, class_names):
    for result in results:
        for box in result.boxes:
            # 바운딩 박스 좌표 추출 (좌상단 x1, y1, 우하단 x2, y2)
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # 바운딩 박스 좌표를 정수로 변환
            conf = box.conf[0]  # 신뢰도
            label = int(box.cls[0])  # 클래스 인덱스 (정수로 변환)

            # 클래스명 변환 (예상 인덱스 범위 확인)
            class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
            
            # 바운딩 박스 그리기(빨간색)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # 라벨과 신뢰도 표시(빨간색)
            cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

# 실시간 객체 감지 실행 함수
def run_detection(model_path, class_names):
    # 모델 및 카메라 초기화
    model = load_model(model_path)
    cap = initialize_camera()

    # 카메라가 열려있는 동안 객체 감지 수행
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("컵라면을 인식할 수 없습니다.")
            break
        
        # 객체 감지 수행
        results = detect_objects(model, frame)
        
        # 감지된 객체에 대한 박스와 라벨 표시
        draw_boxes_and_labels(frame, results, class_names)
        
        # 결과 프레임을 화면에 표시
        cv2.imshow('컵라면 인식', frame)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 자원 해제
    cap.release()
    cv2.destroyAllWindows()

# 메인 함수 호출
if __name__ == "__main__":
    model_path = 'best.pt'  # YOLO 모델 파일 경로
    class_names = [
        'buldak', 'buldak4Cheese', 'buldakCarbo', 'buldakSoup',
        'buldakSoup2', 'carboSoup', 'carboSoup2', 'cheeseSoup',
        'cheeseSoup2', 'jinHot', 'jinHotSoup', 'jinMild', 'jinMildSoup',
        'kaguri', 'kaguriSoup', 'kimchi', 'kimchiSoup', 'kimchiSoup2',
        'king', 'kingSoup', 'kingSoup2', 'ojingeo', 'ojingeoSoup', 'sesame',
        'sesameSoup1', 'sesameSoup2', 'sesameSoup3', 'shin', 'shinSoup',
        'wang', 'wangSoup', 'wangSoup2'
    ]
    
    run_detection(model_path, class_names)
