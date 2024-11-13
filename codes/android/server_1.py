import socket
from PIL import Image
import io
import time

# 서버 설정
UDP_IP = "192.168.0.3"  # 모든 인터페이스에서 수신 대기
UDP_PORT = 8080  # 클라이언트와 동일한 포트 설정
BUFFER_SIZE = 65535  # 최대 UDP 패킷 크기

# UDP 소켓 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(10)  # 10초 동안 수신이 없으면 타임아웃 발생

print("서버가 시작되었습니다...")

# 패킷 수집을 위한 변수 초기화
image_data = bytearray()  # 전체 이미지 데이터를 저장할 바이트 배열
expected_packet = 0  # 현재 기대하는 패킷 번호

try:
    # 여러 패킷 수신
    while True:
        try:
            packet, addr = sock.recvfrom(BUFFER_SIZE)
            print(f"수신한 패킷 크기: {len(packet)} 바이트, 클라이언트 주소: {addr}")

            # 첫 번째 바이트는 패킷 번호로 사용
            packet_number = packet[0]
            packet_data = packet[1:]

            # 패킷 수신 상태 확인
            if packet_number == expected_packet:
                print(f"패킷 {packet_number} 수신 성공.")
                image_data.extend(packet_data)  # 패킷 데이터를 이미지 데이터에 추가
                expected_packet += 1  # 다음 패킷을 기대

                # 마지막 패킷인지 확인 (패킷 크기로 판단하여 종료)
                if len(packet_data) < BUFFER_SIZE - 1:  # 마지막 패킷일 가능성
                    print("마지막 패킷을 수신했습니다.")
                    break
            else:
                print(f"경고: 패킷 {expected_packet}을(를) 기대했으나 패킷 {packet_number} 수신됨!")
                # 누락된 패킷이 있음을 표시
                # 필요시, 재전송 요청을 넣거나, 누락된 패킷을 처리하는 로직을 추가할 수 있음
        except socket.timeout:
            print("수신 대기 중 타임아웃 발생. 클라이언트 연결 확인 필요.")
            break

    # 이미지 변환 및 출력
    try:
        image = Image.open(io.BytesIO(image_data))
        image.show()

        # 이미지 저장 (선택 사항)
        image.save("received_image.png")
        print("이미지 저장 완료")
    except Exception as e:
        print(f"이미지 변환 실패: {e}")

finally:
    sock.close()
    print("서버가 종료되었습니다.")
