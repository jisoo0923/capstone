1. 환경 설정
    - 필요한 패키지:
      - `requests` (HTTP 요청처리) 
      - `pyttsx3` (tts 라이브러리)
    - 설치 명령어:

      ```pip install requests pyttsx3```

   
2. 서버에서 데이터 가져오기
   - requests통해 HTTP요청 처리
     
      ```py
      import requests
      import json
      ...
      server_url = "http://43.203.182.200/getjson.php" # 서버 주소 
      json_data = fetch_data_from_server(server_url) # 서버에서 데이터 불러옴
      ...
      ```
   
3. JSON 데이터를 파싱
    - 데이터를 저장할 빈 리스트를 선언 : db_list = []
    - 데이터의 가공 : 라벨, 이름, 제조사, 레시피

      ```py
      ...
      dbData = DBData()
      dbData.set_member_label(item.get('rabel', 'unknown'))
      dbData.set_member_name(item.get('name', 'unknown'))
      dbData.set_member_maker(item.get('maker', 'unknown'))
      dbData.set_member_recipe(item.get('recipe', 'unknown'))
      db_list.append(dbData) # 항목별 가공된 데이터를 리스트에 추가
      ...
      ```

4. 라벨에 맞는 데이터 존재하는지 찾기
   - db_list에서 일치하는 라벨이 존재하는지 탐색
   - 존재하면 해당 제품의 정보를 반환
   - 없으면 None반환
     ```py
     ...
     # 라벨을 기준으로 데이터베이스에서 제품을 찾는 함수
     def find_product_by_label(label):
     if not db_list:
         print("데이터베이스가 비어 있습니다.")
         return None
     for product in db_list:
         if product.label == label:
             return product
     return None
     ...
     ```
5. 제품 정보를 tts음성으로 안내
    - pyttsx3 통해 텍스트를 음성으로 변환
    - 제품을 발견하면 해당 제품의 정보를 음성으로 안내
    - None을 받으면 오류 메세지를 음성으로 안내
    - product를 매개변수로 제품 정보를 받음
    - speed(기본 200)를 매개변수로 받아 음성 속도 조절 기능
      
        ```py
        ...
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
        ...
        ```
7. 메인함수 동작 과정
      - 주소를 통해 서버에서 json데이터를 요청 : json_data = fetch_data_from_server(server_url)
      - 성공하면 빈 리스트(db_list = [])에 제품 정보를 항목별 텍스트 데이터로 가공해 리스트에 추가 : parse_json_data(json_data)
      - 라벨을 사용자로 부터 입력받음 : label = input("라벨을 입력하세요: ")
      - 라벨 맞는 제품이 존재하는 탐색 : product = find_product_by_label(label)
      - 존재하면 product로 해당 제품 정보를 반환, 존재하지 않으면 None 반환
      - 제품이 존재하면 해당 제품 정보를 지정한 속도로 tts 음성 안내 : speak_product_info(product, speed=200)
      - 제품이 존재하지 않으면 오류 문자를 지정한 속도로 tts 음성 안내 :

8. 주요 기능 설명
      - 주소를 통해 db에서 데이터를 불러오는 기능
      - json데이터를 적절하게 텍스트로 가공하는 기능
      - 라벨에 맞는 데이터를 탐색하는 기능
      - 텍스트를 tts 음성으로 안내하는 기능
