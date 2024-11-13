package com.parkjisoo.ramenrecognitionproject;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
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

    private static final int CAMERA_PERMISSION_REQUEST_CODE = 100;
    private ImageView imageView;  // 캡처된 이미지 표시할 ImageView
    private TextView textViewName, textViewMaker, textViewRecipe;  // 컵라면 정보 텍스트뷰
    private Bitmap capturedImage;  // 캡처된 이미지 저장할 Bitmap 객체

    // ActivityResultLauncher 선언
    private ActivityResultLauncher<Intent> takePictureLauncher;

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

        // 권한 요청 메서드 호출
        requestCameraPermission();

        // 사진 캡처 버튼 클릭 리스너 설정
        captureButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                    dispatchTakePictureIntent();  // 권한이 있을 때 카메라 앱 실행
                } else {
                    Toast.makeText(MainActivity.this, "카메라 권한이 필요합니다.", Toast.LENGTH_SHORT).show();
                    requestCameraPermission();  // 권한이 없으면 권한 요청
                }
            }
        });

        // ActivityResultLauncher 초기화
        takePictureLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    if (result.getResultCode() == RESULT_OK) {
                        Intent data = result.getData();
                        if (data != null && data.getExtras() != null) {
                            // 촬영된 이미지를 번들로부터 가져옴
                            capturedImage = (Bitmap) data.getExtras().get("data");
                            imageView.setImageBitmap(capturedImage);  // ImageView에 캡처된 이미지 표시

                            // 사진을 찍은 후 서버에 자동으로 업로드
                            uploadImageToServer(capturedImage);
                        }
                    }
                }
        );
    }

    // 카메라 권한 요청 메서드
    private void requestCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            // 권한이 부여되지 않은 경우 권한 요청
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST_CODE);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == CAMERA_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // 권한이 허용된 경우
                Toast.makeText(this, "카메라 권한이 허용되었습니다.", Toast.LENGTH_SHORT).show();
            } else {
                // 권한이 거부된 경우
                Toast.makeText(this, "카메라 권한이 필요합니다.", Toast.LENGTH_SHORT).show();
            }
        }
    }

    // 카메라 앱 실행을 위한 인텐트 생성 및 실행 함수
    private void dispatchTakePictureIntent() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
            takePictureLauncher.launch(takePictureIntent);
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
                            .url("http://서버주소/upload")  // 서버 주소로 변경 필요
                            .post(requestBody)
                            .build();

                    // 요청 실행 및 응답 처리
                    Response response = client.newCall(request).execute();
                    if (response.isSuccessful()) {
                        String responseData = response.body().string();
                        runOnUiThread(() -> parseJsonResponse(responseData));  // UI 스레드에서 응답 처리
                    }
                } catch (Exception e) {
                    e.printStackTrace();  // 예외 발생 시 스택 트레이스 출력
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
