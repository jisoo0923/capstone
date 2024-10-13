import requests
import json
import pyttsx3

# 데이터베이스에서 가져온 JSON을 담을 리스트
db_list = []

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

# 서버에서 데이터를 가져오는 함수
def fetch_data_from_server(server_url):
    try:
        response = requests.get(server_url)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"서버 요청 중 오류 발생: {e}")
        return None

# JSON 데이터를 파싱하는 함수
def parse_json_data(json_string):
    try:
        data = json.loads(json_string)
        print("받은 데이터:", data)  # 전체 데이터 출력 (디버깅용)
        
        if 'test' in data and isinstance(data['test'], list):
            for item in data['test']:
                if all(key in item for key in ['rabel', 'name', 'maker', 'recipe']):
                    dbData = DBData()
                    dbData.set_member_label(item.get('rabel', 'unknown'))
                    dbData.set_member_name(item.get('name', 'unknown'))
                    dbData.set_member_maker(item.get('maker', 'unknown'))
                    dbData.set_member_recipe(item.get('recipe', 'unknown'))
                    db_list.append(dbData)
                    
                    print(f"Added data: {item.get('rabel', 'unknown')}, {item.get('name', 'unknown')}, {item.get('maker', 'unknown')}, {item.get('recipe', 'unknown')}")
            print(f"데이터 파싱 성공: {len(db_list)}개 항목 추가됨")
        else:
            print("'test' 키가 없거나 배열이 아닙니다.")
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

# 라벨을 기준으로 데이터베이스에서 제품을 찾는 함수
def find_product_by_label(label):
    if not db_list:
        print("데이터베이스가 비어 있습니다.")
        return None
    for product in db_list:
        if product.label == label:
            return product
    return None

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

# 메인 함수
def main():
    server_url = "http://43.203.182.200/getjson.php"
    json_data = fetch_data_from_server(server_url)
    if json_data:
        parse_json_data(json_data)
        label = input("라벨을 입력하세요: ")
        product = find_product_by_label(label)
        if product:
            print(f"제품명: {product.name}, 제조사: {product.maker}, 조리법: {product.recipe}")
            speak_product_info(product, speed=200)  # 제품 정보를 음성으로 말하기
        else:
            print("해당 라벨의 제품을 찾을 수 없습니다.")
            speak_product_info(None, speed=200)  # 제품을 찾지 못했음을 알리기

# 프로그램 실행
if __name__ == "__main__":
    main()

