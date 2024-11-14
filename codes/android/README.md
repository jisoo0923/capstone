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

### (1). 안드로이드 -> 서버 이미지 업로드 관련
    - 네트워크 보안 정책 수정
        - res/xml 폴더에 `network_security_config.xml` 파일 생성 후 코드 추가
            ```xml
            <?xml version="1.0" encoding="utf-8"?>
            <network-security-config>
                <domain-config cleartextTrafficPermitted="true">
                    <domain includeSubdomains="true">192.168.35.61</domain>
                </domain-config>
            </network-security-config>
            ```
        - `AndroidManifest.xml`에 설정 추가
            ```xml
            <application
                ...
                android:networkSecurityConfig="@xml/network_security_config">
                ...
            </application>





