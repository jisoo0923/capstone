package com.parkjisoo.ramenrecognitionproject;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import com.google.gson.Gson;
import java.io.ByteArrayOutputStream;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_IMAGE_CAPTURE = 1;
    private ImageView imageView;  // 캡처된 이미지 표시할 ImageView
    private TextView textViewName, textViewMaker, textViewRecipe;  // 컵라면 정보 텍스트뷰
    private Bitmap capturedImage;  // 캡처된 이미지 저장할 Bitmap 객체

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // UI 요소 초기화
        imageView = findViewById(R.id.imageView);
        textViewName = findViewById(R.id.textViewName);
        textViewMaker = findViewById(R.id.textViewMaker);
        textViewRecipe = findViewById(R.id.textViewRecipe);
        Button captureButton = findViewById(R.id.captureButton);  // 사진 캡처 버튼

        // 사진 캡처 버튼 클릭 리스너 설정
        captureButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dispatchTakePictureIntent();  // 카메라 앱 실행하여 사진 촬영
            }
        });
    }

    // 카메라 앱 실행을 위한 인텐트 생성 및 실행 함수
    private void dispatchTakePictureIntent() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
    }

    // 사진 촬영 결과 처리 함수
    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
            // 촬영된 이미지를 번들로부터 가져옴
            Bundle extras = data.getExtras();
            capturedImage = (Bitmap) extras.get("data");
            imageView.setImageBitmap(capturedImage);  // ImageView에 캡처된 이미지 표시

            // 사진을 찍은 후 서버에 자동으로 업로드
            uploadImageToServer(capturedImage);
        }
    }

    // 서버로 이미지 업로드 함수
    private void uploadImageToServer(Bitmap bitmap) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // 이미지를 JPEG 형식으로 압축하고 바이트 배열로 변환
                    ByteArrayOutputStream stream = new ByteArrayOutputStream();
                    bitmap.compress(Bitmap.CompressFormat.JPEG, 100, stream);
                    byte[] byteArray = stream.toByteArray();

                    // OkHttpClient 객체 생성
                    OkHttpClient client = new OkHttpClient();

                    // 요청 바디 생성: 이미지 파일을 포함한 멀티파트 요청
                    RequestBody requestBody = new MultipartBody.Builder()
                            .setType(MultipartBody.FORM)
                            .addFormDataPart("image", "cup_ramen.jpg",
                                    RequestBody.create(MediaType.parse("image/jpeg"), byteArray))
                            .build();

                    // 요청 객체 생성: 서버 URL 설정 및 POST 요청
                    Request request = new Request.Builder()
                            .url("http://192.168.10.101:8080")  // 로컬 서버 주소로 변경 필요
                            .post(requestBody)
                            .build();

                    // 요청 실행 및 응답 처리
                    Response response = client.newCall(request).execute();
                    if (response.isSuccessful()) {
                        String responseData = response.body().string();
                        runOnUiThread(() -> {
                            parseJsonResponse(responseData);
                            Toast.makeText(MainActivity.this, "서버 응답 수신 성공", Toast.LENGTH_SHORT).show();
                        });  // UI 스레드에서 응답 처리
                    } else {
                        runOnUiThread(() -> {
                            Toast.makeText(MainActivity.this, "서버 응답 실패", Toast.LENGTH_SHORT).show();
                        });
                    }
                } catch (Exception e) {
                    e.printStackTrace();  // 예외 발생 시 스택 트레이스 출력
                    runOnUiThread(() -> {
                        Toast.makeText(MainActivity.this, "이미지 업로드 중 오류 발생", Toast.LENGTH_SHORT).show();
                    });
                }
            }
        }).start();
    }


    // 서버에서 받은 JSON 응답을 파싱하여 화면에 출력하는 함수
    private void parseJsonResponse(String jsonData) {
        Gson gson = new Gson();
        CupRamenInfo cupRamenInfo = gson.fromJson(jsonData, CupRamenInfo.class);

        // 파싱된 데이터를 TextView에 설정
        textViewName.setText("제품명: " + cupRamenInfo.getName());
        textViewMaker.setText("제조사: " + cupRamenInfo.getMaker());
        textViewRecipe.setText("조리법: " + cupRamenInfo.getRecipe());
    }

    // 컵라면 정보 클래스: 서버에서 받은 JSON 데이터를 매핑하기 위한 클래스
    public class CupRamenInfo {
        private String label;
        private String name;
        private String maker;
        private String recipe;

        public String getName() {
            return name;
        }

        public String getMaker() {
            return maker;
        }

        public String getRecipe() {
            return recipe;
        }
    }
}
