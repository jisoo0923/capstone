import cv2
from ultralytics import YOLO

# 1. 모델 로딩 함수
def load_model(model_path):
    """
    학습한 YOLOv8 모델을 불러옵니다.
    :param model_path: 모델 파일 경로
    :return: YOLO 모델 객체
    """
    return YOLO(model_path)

# 2. 카메라 초기화 함수
def initialize_camera():
    """
    내장 카메라를 초기화합니다.
    :return: 카메라 객체
    """
    return cv2.VideoCapture(0)

# 3. 객체 감지 함수
def detect_objects(model, frame):
    """
    YOLO 모델을 사용하여 객체를 감지합니다.
    :param model: YOLO 모델 객체
    :param frame: 카메라 프레임 이미지
    :return: 감지된 객체 결과
    """
    return model(frame)

# 4. 박스와 라벨 그리기 함수
def draw_boxes_and_labels(frame, results, class_names):
    """
    감지된 객체에 대한 바운딩 박스와 라벨을 프레임에 그립니다.
    :param frame: 카메라 프레임 이미지
    :param results: YOLO 감지 결과
    :param class_names: 클래스 이름 리스트
    """
    for result in results:
        for box in result.boxes:
            # 바운딩 박스 좌표 추출 (좌상단 x1, y1, 우하단 x2, y2)
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # 바운딩 박스 좌표를 정수로 변환
            conf = box.conf[0]  # 신뢰도
            label = int(box.cls[0])  # 클래스 인덱스 (정수로 변환)

            # 클래스명 변환 (예상 인덱스 범위 확인)
            class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
            
            # 바운딩 박스 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # 라벨과 신뢰도 표시
            cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

# 5. 실시간 객체 감지 실행 함수
def run_detection(model_path, class_names):
    """
    카메라를 통해 실시간 객체 감지를 수행합니다.
    :param model_path: YOLO 모델 파일 경로
    :param class_names: 클래스 이름 리스트
    """
    # 모델 및 카메라 초기화
    model = load_model(model_path)
    cap = initialize_camera()

    # 카메라가 열려있는 동안 객체 감지 수행
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("캠에서 사진을 가져올 수 없습니다.")
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
