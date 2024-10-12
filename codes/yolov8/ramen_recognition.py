import cv2
from ultralytics import YOLO

# 학습한 YOLOv8 모델 불러오기 (경로 지정)
model = YOLO('best.pt')  # 학습된 모델 파일 경로 지정 (PyTorch 형태)

# 내장캠 사용
cap = cv2.VideoCapture(0)

# 캠이 열려있는 동안 반복
while cap.isOpened():
    ret, frame = cap.read()
    
    if not ret:
        print("캠에서 사진을 가져올 수 없습니다.")
        break
    
    # YOLO 모델로 캠 프레임 추론
    results = model(frame)

    # 결과에서 바운딩 박스, 클래스, 신뢰도 추출 및 표시
    for box in results[0].boxes:  # 각 객체의 바운딩 박스 정보 가져오기
        # 바운딩 박스 좌표 추출 (좌상단 x1, y1, 우하단 x2, y2)
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # 바운딩 박스 좌표를 정수로 변환
        conf = box.conf[0]  # 신뢰도
        label = int(box.cls[0])  # 클래스 인덱스 (정수로 변환)

        # [옵션] label 인덱스를 클래스명으로 변환 가능
        class_names = ['buldak', 'buldak4Cheese', 'buldakCarbo', 'buldakSoup',
                       'buldakSoup2', 'carboSoup', 'carboSoup2', 'cheeseSoup',
                       'cheeseSoup2', 'jinHot', 'jinHotSoup', 'jinMild', 'jinMildSoup',
                       'kaguri', 'kaguriSoup', 'kimchi', 'kimchiSoup', 'kimchiSoup2',
                       'king', 'kingSoup', 'kingSoup2', 'ojingeo', 'ojingeoSoup', 'sesame',
                       'sesameSoup1', 'sesameSoup2', 'sesameSoup3', 'shin', 'shinSoup',
                       'wang', 'wangSoup', 'wangSoup2']  # 예시 클래스명
        class_name = class_names[label] if label < len(class_names) else f'Unknown({label})'
        
        # 바운딩 박스 그리기
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 라벨과 신뢰도 표시
        cv2.putText(frame, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    
    # 결과 프레임을 화면에 표시
    cv2.imshow('컵라면 인식', frame)
    
    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()