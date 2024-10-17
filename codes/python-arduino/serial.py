import serial
import time

py_serial = serial.Serial(
    
    # Window
    port='COM9',
    
    # 보드 레이트 (통신 속도)
    baudrate=9600,
)

flag=False      #기준 무게 입력 확인

while True:
    
    if(not flag):      #기준 무게(물 용량) 입력
        weight = input('무게 입력:')
        flag=True;
        

    py_serial.write(weight.encode())     #입력받은 무게 인코딩 후 아두이노로 송신
    
    #time.sleep(0.1)
    
    if py_serial.readable():
        
        # 들어온 값이 있으면 값을 한 줄 읽음 (BYTE 단위로 받은 상태)
        response = py_serial.readline()
        
        #디코딩 후 출력 (가장 끝의 \n을 없애주기위해 슬라이싱 사용)
        print(response[:len(response)-1].decode())
