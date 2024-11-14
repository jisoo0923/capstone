## 0. 진행상황 정리

### (1) 안드로이드 -> 서버
  - ✅ 이미지 전송 성공
  - ✅ 서버 내 이미지 저장 성공
### (2) 서버 -> 안드로이드
  - ✅ 모델 분석결과 전송 성공
      - `name`, `maker`, `recipe`


## 1. strings.xml
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

## 2. build.gradle
- dependencies에 추가
  
```
implementation("com.google.code.gson:gson:2.8.8")
implementation("com.squareup.okhttp3:okhttp:4.9.1")
```

## 3. 서버 코드 수정

### (1) 안드로이드 -> 서버 이미지 업로드 관련(HTTP 통신)
- 네트워크 보안 정책 수정
  - res/xml 폴더에 network_security_config.xml 파일 생성 후 코드 추가
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
            
  - AndroidManifest.xml에 설정 추가   
    ```xml
        <?xml version="1.0" encoding="utf-8"?>
        <manifest xmlns:android="http://schemas.android.com/apk/res/android"
            xmlns:tools="http://schemas.android.com/tools"
            package="com.parkjisoo.ramenrecognitionproject" >

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
    - `AndroidManifest.xml` 파일 내 `package="com.parkjisoo.ramenrecognitionproject" >` 수정하세요.
    - 설치 목록
      - `ultralytics`, `flask`, `Flask-CORS`

