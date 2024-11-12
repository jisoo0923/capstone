package com.cookandroid.mobile_test01;

import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.provider.MediaStore;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;

import java.io.ByteArrayOutputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_IMAGE_CAPTURE = 1;  // 카메라 요청 코드
    private static final int CAMERA_PERMISSION_REQUEST_CODE = 100;  // 권한 요청 코드

    private Bitmap capturedImage;  // 캡처된 이미지를 저장할 변수
    private ImageView imageView;  // 이미지를 표시할 ImageView

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 카메라 권한 체크
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST_CODE);
            }
        }

        // ImageView 및 버튼 초기화
        imageView = findViewById(R.id.imageView);
        Button buttonCapture = findViewById(R.id.buttonCapture);
        Button buttonSend = findViewById(R.id.buttonSend);

        // 버튼 클릭 시 카메라 실행
        buttonCapture.setOnClickListener(v -> {
            Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
        });

        // 이미지 전송 버튼 클릭 시
        buttonSend.setOnClickListener(v -> {
            if (capturedImage != null) {
                sendImage(capturedImage, "192.168.56.1", 5005);  // 이미지 전송
            } else {
                Toast.makeText(MainActivity.this, "이미지를 먼저 캡처하세요", Toast.LENGTH_SHORT).show();
            }
        });
    }

    // 카메라 권한 요청 결과 처리
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == CAMERA_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // 권한이 승인됨
                Toast.makeText(this, "카메라 권한이 승인되었습니다.", Toast.LENGTH_SHORT).show();
            } else {
                // 권한이 거부됨
                Toast.makeText(this, "카메라 권한이 필요합니다.", Toast.LENGTH_SHORT).show();
            }
        }
    }

    // ActivityResult 처리 (카메라 촬영 후 결과 처리)
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
            if (data != null && data.getExtras() != null) {
                Bitmap imageBitmap = (Bitmap) data.getExtras().get("data");
                capturedImage = imageBitmap;  // capturedImage에 저장
                imageView.setImageBitmap(imageBitmap);  // ImageView에 표시
            }
        }
    }

    // 이미지 전송 기능
    private void sendImage(Bitmap bitmap, String serverIp, int serverPort) {
        new Thread(() -> {
            DatagramSocket socket = null;
            try {
                // 이미지 비트맵을 바이트 배열로 변환
                ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
                bitmap.compress(Bitmap.CompressFormat.PNG, 100, byteArrayOutputStream);
                byte[] imageData = byteArrayOutputStream.toByteArray();

                // 소켓 열기
                socket = new DatagramSocket();
                InetAddress serverAddress = InetAddress.getByName(serverIp);

                // 이미지 데이터 전송
                DatagramPacket packet = new DatagramPacket(imageData, imageData.length, serverAddress, serverPort);
                socket.send(packet);

                runOnUiThread(() -> {
                    Toast.makeText(MainActivity.this, "이미지 전송 완료", Toast.LENGTH_SHORT).show();
                });
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "이미지 전송 실패", Toast.LENGTH_SHORT).show());
            } finally {
                if (socket != null && !socket.isClosed()) {
                    socket.close();  // 소켓 닫기
                }
            }
        }).start();
    }
}
