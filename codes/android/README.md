### 0. 진행상황 정리

- (1) 안드로이드 -> 서버
  - ✅ 이미지 전송 성공
  - ✅ 서버 내 이미지 저장 성공
- (2) 서버 -> 안드로이드
  - ✅ JSON 데이터 전송 성공
      - `name`, `maker`, `recipe`
  - 결과 이미지
    
      <img width="1008" alt="스크린샷 2024-11-15 오전 10 57 32" src="https://github.com/user-attachments/assets/237e9d66-7062-4398-868f-f02f814025c2">
      <img width="414" alt="스크린샷 2024-11-15 오전 11 08 20" src="https://github.com/user-attachments/assets/2c090b96-0746-402f-b1f1-e1f9c79976a5">



- (3) 안드로이드 TTS
  - ✅ 제품명, 제조사, 조리법 음성출력 성공
  - 물 다 붓고난 후 음성 출력 코드 추가필요
<br>

- (4) 아두이노 프로그래밍
  - `START()`, `STOP()` 코드 수정 필요: 핀번호 주의
  - 펌프 동작 시점 고려: 무게 측정과 동시? 일정 시간후 자동? 수동? 
  - 펌프 코드와 무게측정 코드의 충돌 확인필요 (무게측정 중 펌프가 멈추거나, 또는 그 반대)
  - 릴레이 모듈 사용하지 않으면 제거 고려
- (5) 전체 연동
  - ✅ 안드로이드 -> 서버 이미지 전송 및 저장
  - ✅ 서버 내 모델 인식
  - ✅ 서버 -> DB 해당 컵라면 라벨로 4개 JSON 데이터 받기
  - ✅ 서버 -> 안드로이드 3개 데이터 전송 및 음성 안내
    - 제품명, 제조사, 조리법
  - ✅ 서버 -> 아두이노 1개 데이터 전송
    - 물의 양(volume)
  - 서버 -> 아두이노 실시간 물 측정 및 도달 시 완료메시지
    - ✅ 서버 메시지 출력
    - 서버 -> 안드로이드 TTS 음성안내 `물을 다 따랐습니다.`






<br>

- (6) WIFI 연결 테스트
  - ✅ WIFI6
  - ✅ 아름님 핫스팟



<br>

### 1. strings.xml
```xml
<resources>
    <string name="app_name">Ramen Recognition Project</string>
    <string name="captured_image">Captured Image</string>
    <string name="capture_button_text">Capture Image</string>
    <string name="label_product_name">제품명: </string>
    <string name="label_maker">제조사: </string>
    <string name="label_recipe">조리법: </string>
</resources>
```

### 2. build.gradle
- `dependencies`에 추가
  
```
implementation("com.google.code.gson:gson:2.8.8")
implementation("com.squar3.3.eup.okhttp3:okhttp:4.9.1")
```

### 3. 서버와의 네트워크 통신 설정

- (1) 안드로이드 -> 서버 이미지 업로드 관련(HTTP 통신)
  - 네트워크 보안 정책 수정
    - `res/xml` 폴더에 `network_security_config.xml` 파일 생성 후 코드 추가
      ```xml
          <?xml version="1.0" encoding="utf-8"?>
              <network-security-config>
                  <domain-config cleartextTrafficPermitted="true">
                      <!-- 서버 주소는 변경 필요 -->
                      <domain includeSubdomains="true">192.168.35.61</domain>
                  </domain-config>
                  <base-config cleartextTrafficPermitted="true" />
              </network-security-config>
      ```
            
    - `AndroidManifest.xml`에 설정 추가   
      ```xml
        <?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            xmlns:tools="http://schemas.android.com/tools"

            package="com." >

            <!-- 필수 권한 설정 -->
            <uses-permission android:name="android.permission.INTERNET" />
            <uses-permission android:name="android.permission.CAMERA" />
            <uses-feature android:name="android.hardware.camera" android:required="true" />

            <application
                android:allowBackup="true"
                android:dataExtractionRules="@xml/data_extraction_rules"
                android:fullBackupContent="@xml/backup_rules"
                android:icon="@mipmap/ic_launcher"
                android:label="@string/app_name"
                android:roundIcon="@mipmap/ic_launcher_round"
                android:supportsRtl="true"
                android:theme="@style/Theme.RamenRecognitionProject"
                tools:targetApi="31"

                android:networkSecurityConfig="@xml/network_security_config"
                android:usesCleartextTraffic="true">
        
                <activity
                    android:name=".MainActivity"
                    android:exported="true">
                    <intent-filter>
                        <action android:name="android.intent.action.MAIN" />
                        <category android:name="android.intent.category.LAUNCHER" />
                    </intent-filter>
                </activity>

            </application>

        </manifest>

      ```

    - 안드로이드 실행 시 주의사항
      - `uploadImageToServer()` 메서드 내 서버 URL을 수정하세요.
      - `network_security_config.xml` `<domain>` 태그에서 IP주소 수정하세요.
      - 설치 목록
        - `ultralytics`, `pyttsx3`, `opencv-python`, `pyserial`, `requests`, `flask`, `Flask-CORS`

