import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.provider.MediaStore;
import android.speech.tts.TextToSpeech;
import android.speech.tts.TextToSpeech.OnInitListener;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.google.gson.Gson;

import java.io.ByteArrayOutputStream;
import java.util.Locale;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity implements OnInitListener {

    private static final int REQUEST_IMAGE_CAPTURE = 1;
    private ImageView imageView;  // 캡처된 이미지 표시할 ImageView
    private TextView textViewName, textViewMaker, textViewRecipe;  // 컵라면 정보 텍스트뷰
    private Bitmap capturedImage;  // 캡처된 이미지 저장할 Bitmap 객체
    private TextToSpeech textToSpeech;  // TTS 객체
    private OkHttpClient client;  // OkHttpClient 객체

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

        // TTS 초기화
        textToSpeech = new TextToSpeech(this, this);

        // OkHttpClient 초기화
        client = new OkHttpClient();

        // 사진 캡처 버튼 클릭 리스너 설정
        captureButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                dispatchTakePictureIntent();  // 카메라 앱 실행하여 사진 촬영
            }
        });

        // 목표 무게 도달 확인 함수 호출
        new Thread(this::checkTargetWeightReached).start();
    }

    // TTS 초기화 완료 후 호출되는 콜백
    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            int langResult = textToSpeech.setLanguage(Locale.KOREAN);  // 한국어 설정
            if (langResult == TextToSpeech.LANG_MISSING_DATA || langResult == TextToSpeech.LANG_NOT_SUPPORTED) {
                Toast.makeText(this, "한국어 TTS가 지원되지 않습니다.", Toast.LENGTH_SHORT).show();
            }
        } else {
            Toast.makeText(this, "TTS 초기화 실패", Toast.LENGTH_SHORT).show();
        }
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

                    // 요청 바디 생성: 이미지 파일을 포함한 멀티파트 요청
                    RequestBody requestBody = new MultipartBody.Builder()
                            .setType(MultipartBody.FORM)
                            .addFormDataPart("image", "cup_ramen.jpg",
                                    RequestBody.create(MediaType.parse("image/jpeg"), byteArray))
                            .build();

                    // 요청 객체 생성: 서버 URL 설정 및 POST 요청
                    Request request = new Request.Builder()
                            .url("http://192.168.101.7:8080")  // 로컬 서버 주소로 변경 필요
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
        ServerResponse response = gson.fromJson(jsonData, ServerResponse.class);

        if (response != null && "success".equals(response.getStatus())) {
            ProductInfo productInfo = response.getProductInfo();
            if (productInfo != null) {
                // 텍스트 출력
                textViewName.setText("제품명: " + productInfo.getName());
                textViewMaker.setText("제조사: " + productInfo.getMaker());
                textViewRecipe.setText("조리법: " + productInfo.getRecipe());

                // TTS로 읽어주기
                String ttsText = "제품명은 " + productInfo.getName() + ", 제조사는 " + productInfo.getMaker() + ", 조리법은 " + productInfo.getRecipe() + "입니다.";
                textToSpeech.speak(ttsText, TextToSpeech.QUEUE_FLUSH, null, null);
            } else {
                textViewName.setText("제품 정보를 찾을 수 없습니다.");
                textViewMaker.setText("");
                textViewRecipe.setText("");
            }
        } else {
            textViewName.setText("서버 응답 실패: " + (response != null ? response.getMessage() : "알 수 없는 오류"));
            textViewMaker.setText("");
            textViewRecipe.setText("");
        }
    }

    // 목표 무게 도달 확인 함수 (서버로부터 알림 수신)
    private void checkTargetWeightReached() {
        try {
            // 서버에 요청 보내기 (목표 무게 도달 여부 확인)
            Request request = new Request.Builder()
                    .url("http://43.203.182.200:50505/checkWeightReached")  // 서버에서 목표 무게 도달 여부 확인하는 엔드포인트
                    .build();

            while (true) {
                Response response = client.newCall(request).execute();
                if (response.isSuccessful()) {
                    String responseData = response.body().string();
                    ServerResponse serverResponse = new Gson().fromJson(responseData, ServerResponse.class);

                    if (serverResponse != null && "success".equals(serverResponse.getStatus())) {
                        // 목표 무게에 도달했음을 확인한 경우
                        runOnUiThread(() -> {
                            Toast.makeText(MainActivity.this, "목표 무게에 도달했습니다.", Toast.LENGTH_SHORT).show();
                            textToSpeech.speak("물을 다 부었습니다.", TextToSpeech.QUEUE_FLUSH, null, null);
                        });
                        break;
                    }
                }
                Thread.sleep(5000);  // 5초마다 확인
            }
        } catch (Exception e) {
            e.printStackTrace();
            runOnUiThread(() -> Toast.makeText(MainActivity.this, "목표 무게 확인 중 오류 발생", Toast.LENGTH_SHORT).show());
        }
    }

    // 서버 응답 클래스: JSON 응답을 매핑하기 위한 클래스
    public class ServerResponse {
        private String status;
        private String message;
        private ProductInfo product_info;

        public String getStatus() {
            return status;
        }

        public String getMessage() {
            return message;
        }

        public ProductInfo getProductInfo() {
            return product_info;
        }
    }

    // 제품 정보 클래스: 서버에서 받은 JSON 데이터를 매핑하기 위한 클래스
    public class ProductInfo {
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

    @Override
    protected void onDestroy() {
        // TTS 객체 해제
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        super.onDestroy();
    }
}
