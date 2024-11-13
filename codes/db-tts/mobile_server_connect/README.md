### 1. activity_main.xml
- 이미지뷰: 촬영 사진 화면출력
- 촬영 버튼: 클릭시 카메라 앱 실행
- 전송 버튼: 클릭시 촬영 사진 서버로 전송   
  
### 2. AndroidManifest.xml
- 인터넷, 카메라 권한승인 필요
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
```

### 3. MainActivity.java
- 촬영 버튼 리스너: 결과를 반환하는 인텐트를 생성하여 디바이스 자체 카메라 앱 실행
  ```java
  buttonCapture.setOnClickListener(v -> {
            Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
        });
  ```
  
- 전송 버튼 리스너: 촬영 사진 존재하면 sendImage(전송할사진, 주소, 포트번호) 실행 
  ```java
  buttonSend.setOnClickListener(v -> {
            if (capturedImage != null) {
                sendImage(capturedImage, "192.168.56.1", 5005);  // 이미지 전송
            } else {
                Toast.makeText(MainActivity.this, "이미지를 먼저 캡처하세요", Toast.LENGTH_SHORT).show();
            }
        });
  ```
- sendImage(전송할 사진, 주소, 포트번호): 이미지를 바이트 배열로 변화하여 전송시도, 새로운 소켓을 열고 해당 주소로 이미지 배열을 전송
  - 해당 주소가 존재하고 포트가 유효하면 전송 성공 but 서버에서의 성공은 보장하지 않는다(그냥 던지고 끝)
  - 주소는 서버의 실제 주소(클라이언트의 주소가 아니다)
  - 모바일 성공, 서버 실패시: 서버의 방화벽, 백그라운드 보안 소프트웨어가 돌아가는지 확인필요
 
### 4. server_test01.py
- 소켓 자체는 파이썬 표준 라이브러리로 추가 작업필요 없음
- 소켓 사용한 PIL이미지 처리를 위한 추가 설치
  ```bash
  pip install pillow
  ```
- 적당한 주소와 포트 번호 설정, 소켓으로 전송 받을 데이터의 크기 설정
  ```py
  UDP_IP = "192.168.56.1" # 주소 변경 필요
  UDP_PORT = 5005 # 적당한 포트 설정 필요
  BUFFER_SIZE = 65535 
  ```
- 실제 데이터 수신 메서드
  ```py
  data, addr = sock.recvfrom(BUFFER_SIZE)
  print(f"수신한 데이터 크기: {len(data)} 바이트")
  ```
  - sock.recvfrom(BUFFER_SIZE): 소켓 객체 sock을 통해 데이터를 수신하는 메서드
  - BUFFER_SIZE는 수신할 수 있는 최대 바이트 수를 지정하는 변수. 이 크기만큼 데이터를 한 번에 수신할 수 있다.
  - 반환 값은 두 개의 요소로 구성됩니다:
    - data: 수신된 데이터 (바이트 형태).
    - addr: 데이터를 보낸 송신자의 주소 (IP와 포트).
- 추가 작업
  - 주소 찾기
    ```cmd
    cmd 창에서
    
    'ipconfig'

    를 입력한다
    192.168.~.~가 서버에서 사용가능한 실제 주소이다
    ```
  - 서버는 데이터를 수신받기 위해 방화벽, 백그라운드 보안 소프트웨어 사용을 중지해야 한다
