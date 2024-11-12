import socket
from PIL import Image
import io

# 서버 설정
UDP_IP = "192.168.56.1" # 주소 변경 필요
UDP_PORT = 5005 # 적당한 포트 설정 필요
BUFFER_SIZE = 65535 

# UDP 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("서버가 시작되었습니다...")

# 데이터 수신 및 이미지 출력
data, addr = sock.recvfrom(BUFFER_SIZE)
print(f"수신한 데이터 크기: {len(data)} 바이트")

# 이미지 변환 및 출력
image = Image.open(io.BytesIO(data))
image.show()

# 이미지 저장 (선택 사항)
image.save("received_image.png")
print("이미지 저장 완료")
