package com.example.myapplication;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.Vibrator;
import android.provider.MediaStore;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.gson.Gson;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.Locale;

import fi.iki.elonen.NanoHTTPD;
import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity implements TextToSpeech.OnInitListener {

    // 사진 촬영 요청 코드
    private static final int REQUEST_IMAGE_CAPTURE = 1;

    // UI 구성 요소
    private TextView textViewName, textViewMaker, textViewRecipe; // 제품명, 제조사, 조리법 표시용 텍스트뷰
    private TextToSpeech textToSpeech; // TTS 객체
    private SpeechRecognizer speechRecognizer; // 음성 인식 객체
    private Intent speechRecognizerIntent; // 음성 인식 Intent
    private Vibrator vibrator; // 버튼 클릭 시 진동 제공

    // 권한 요청 코드
    private static final int CAMERA_PERMISSION_REQUEST_CODE = 100;
    private static final int AUDIO_PERMISSION_REQUEST_CODE = 101;

    // 라면 정보 저장 변수
    private String name = "";   // 제품명
    private String maker = "";  // 제조사
    private String recipe = ""; // 조리법
    private String price = "";  // 가격

    // TTS 속도 기본값
    private float ttsSpeed = 1.0f;

    /**
     * onCreate: 앱 실행 시 호출되며 초기화 작업을 진행합니다.
     */
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 필수 권한 확인 및 요청
        checkRequiredPermissions();

        // 로컬 IP 구성 및 서버로 전달
        configureDynamicIp();

        // UI 요소 초기화
        textViewName = findViewById(R.id.textViewName);
        textViewMaker = findViewById(R.id.textViewMaker);
        textViewRecipe = findViewById(R.id.textViewRecipe);

        // 버튼 초기화
        Button captureButton = findViewById(R.id.captureButton); // 사진 촬영 버튼
        Button listenButton = findViewById(R.id.listenButton);   // 음성 명령 버튼
        ImageButton ttsCtlSlow = findViewById(R.id.ttsCtlSlow);  // TTS 느리게 버튼
        ImageButton ttsCtlRestart = findViewById(R.id.ttsCtlRestart); // TTS 다시 듣기 버튼
        ImageButton ttsCtlFast = findViewById(R.id.ttsCtlFast);  // TTS 빠르게 버튼

        // TTS 초기화
        textToSpeech = new TextToSpeech(this, this);

        // 진동 객체 초기화
        vibrator = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);

        // HTTP 서버 시작
        try {
            HTTPServer server = new HTTPServer(8080);
            server.start(); // 8080 포트에서 서버 실행
            Log.d("HTTPServer", "NanoHTTPD 서버가 실행 중입니다.");
            Toast.makeText(this, "HTTP 서버가 실행 중입니다.", Toast.LENGTH_SHORT).show();
        } catch (IOException e) {
            Log.e("MainActivity", "서버 시작 실패", e);
            Toast.makeText(this, "서버 시작 실패", Toast.LENGTH_SHORT).show();
        }

        // 공통 클릭 리스너 추가 (진동 기능 포함)
        View.OnClickListener buttonClickListener = v -> vibrate(100);

        // 캡처 버튼 클릭 이벤트
        captureButton.setOnClickListener(v -> {
            buttonClickListener.onClick(v);
            dispatchTakePictureIntent(); // 카메라 실행
        });

        // 음성 명령 버튼 클릭 이벤트
        listenButton.setOnClickListener(v -> {
            buttonClickListener.onClick(v);
            if (textToSpeech != null && textToSpeech.isSpeaking()) {
                textToSpeech.stop(); // 현재 실행 중인 TTS 중지
            }
            startListening(); // 음성 인식 시작
        });

        // TTS 속도 조절 버튼들
        ttsCtlSlow.setOnClickListener(v -> {
            buttonClickListener.onClick(v);
            adjustTtsSpeed(-0.25f); // 속도 느리게
        });

        ttsCtlFast.setOnClickListener(v -> {
            buttonClickListener.onClick(v);
            adjustTtsSpeed(0.25f); // 속도 빠르게
        });

        ttsCtlRestart.setOnClickListener(v -> {
            buttonClickListener.onClick(v);
            readRamenInfo(); // 라면 정보 읽기
        });

        // 음성 인식 초기화
        initSpeechRecognizer();
    }

    /**
     * TTS 초기화 완료 후 호출되는 콜백 메서드.
     */
    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS) {
            textToSpeech.setLanguage(Locale.KOREAN); // TTS 언어를 한국어로 설정
            textToSpeech.setSpeechRate(ttsSpeed);    // 기본 속도 설정
        } else {
            Toast.makeText(this, "TTS 초기화 실패", Toast.LENGTH_SHORT).show();
        }
    }

    /**
     * 앱 실행 시 필요한 권한을 확인하고, 없으면 요청합니다.
     */
    private void checkRequiredPermissions() {
        String[] permissions = {
                android.Manifest.permission.RECORD_AUDIO, // 음성 녹음 권한
                android.Manifest.permission.CAMERA        // 카메라 권한
        };

        ArrayList<String> permissionsToRequest = new ArrayList<>();
        for (String permission : permissions) {
            if (ContextCompat.checkSelfPermission(this, permission) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(permission);
            }
        }

        // 요청해야 할 권한이 있다면 한꺼번에 요청
        if (!permissionsToRequest.isEmpty()) {
            ActivityCompat.requestPermissions(this, permissionsToRequest.toArray(new String[0]), 0);
        }
    }

    /**
     * 카메라 앱 실행을 위한 Intent를 생성합니다.
     */
    private void dispatchTakePictureIntent() {
        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
            startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
        } else {
            Toast.makeText(this, "카메라 앱을 실행할 수 없습니다.", Toast.LENGTH_SHORT).show();
        }
    }

    /**
     * 사진 촬영 후 결과를 처리하여 서버로 업로드합니다.
     */
    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
            Bundle extras = data.getExtras();
            Bitmap capturedImage = (Bitmap) extras.get("data");
            uploadImageToServer(capturedImage); // 서버로 이미지 업로드
        }
    }

    /**
     * 로컬 IP 주소를 서버에 전달합니다.
     */
    private void configureDynamicIp() {
        String localIp = getLocalIpAddress();
        if (localIp != null) {
            sendIpToServer(localIp); // IP 전달
        } else {
            Toast.makeText(this, "로컬 IP를 가져올 수 없습니다.", Toast.LENGTH_SHORT).show();
        }
    }

    /**
     * 현재 기기의 로컬 IP 주소를 반환합니다.
     */
    private String getLocalIpAddress() {
        try {
            for (Enumeration<NetworkInterface> en = NetworkInterface.getNetworkInterfaces(); en.hasMoreElements(); ) {
                NetworkInterface intf = en.nextElement();
                for (Enumeration<InetAddress> enumIpAddr = intf.getInetAddresses(); enumIpAddr.hasMoreElements(); ) {
                    InetAddress inetAddress = enumIpAddr.nextElement();
                    if (!inetAddress.isLoopbackAddress() && inetAddress instanceof Inet4Address) {
                        return inetAddress.getHostAddress();
                    }
                }
            }
        } catch (SocketException ex) {
            Log.e("IPConfig", ex.toString());
        }
        return null;
    }

    /**
     * 서버에 로컬 IP를 전달하는 메서드
     */
    private void sendIpToServer(String ipAddress) {
        OkHttpClient client = new OkHttpClient();
        RequestBody body = RequestBody.create(
                MediaType.parse("application/json"),
                "{\"ip\":\"" + ipAddress + "\"}" // IP를 JSON 형태로 전달
        );

        Request request = new Request.Builder()
                .url("http://192.168.229.143:8080/set_android_ip") // 서버 URL
                .post(body)
                .build();

        // 서버 응답 처리
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.e("IPUpdate", "서버에 IP 전달 실패: " + e.getMessage());
                runOnUiThread(() ->
                        Toast.makeText(MainActivity.this, "IP 설정 실패: " + e.getMessage(), Toast.LENGTH_SHORT).show()
                );
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    Log.d("IPUpdate", "서버에 IP 전달 성공");
                    runOnUiThread(() ->
                            Toast.makeText(MainActivity.this, "IP 설정 성공!", Toast.LENGTH_SHORT).show()
                    );
                } else {
                    Log.e("IPUpdate", "서버에 IP 전달 실패: " + response.message());
                    runOnUiThread(() ->
                            Toast.makeText(MainActivity.this, "IP 설정 실패: " + response.message(), Toast.LENGTH_SHORT).show()
                    );
                }
            }
        });
    }

    /**
     * 서버로 이미지를 업로드하는 메서드
     */
    private void uploadImageToServer(Bitmap bitmap) {
        new Thread(() -> {
            try {
                ByteArrayOutputStream stream = new ByteArrayOutputStream();
                bitmap.compress(Bitmap.CompressFormat.JPEG, 100, stream); // 이미지를 JPEG로 압축
                byte[] byteArray = stream.toByteArray();

                OkHttpClient client = new OkHttpClient();
                String serverUrl = "http://" + getServerIp() + ":8080"; // 서버 URL 동적 생성
                RequestBody requestBody = new MultipartBody.Builder()
                        .setType(MultipartBody.FORM)
                        .addFormDataPart("image", "cup_ramen.jpg", RequestBody.create(MediaType.parse("image/jpeg"), byteArray))
                        .build();

                Request request = new Request.Builder()
                        .url(serverUrl)
                        .post(requestBody)
                        .build();

                // 서버 응답 처리
                Response response = client.newCall(request).execute();
                if (response.isSuccessful()) {
                    String responseData = response.body().string();
                    runOnUiThread(() -> parseJsonResponse(responseData)); // 응답 처리
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }

    /**
     * 서버 IP를 반환하는 메서드 (동적 IP 관리 가능)
     */
    private String getServerIp() {
        return "192.168.229.143"; // 기본값 설정
    }

    /**
     * 서버 응답(JSON)을 파싱하여 UI를 업데이트하는 메서드
     */
    private void parseJsonResponse(String jsonData) {
        Gson gson = new Gson();
        ServerResponse response = gson.fromJson(jsonData, ServerResponse.class);

        if (response != null && "success".equals(response.getStatus())) {
            ProductInfo productInfo = response.getProductInfo();
            if (productInfo != null) {
                // 서버에서 받은 데이터를 저장 및 UI 업데이트
                name = productInfo.getName();
                maker = productInfo.getMaker();
                recipe = productInfo.getRecipe();
                price = "정보 없음";  // 가격 정보가 없으므로 기본값 설정

                textViewName.setText("제품명: " + name);
                textViewMaker.setText("제조사: " + maker);
                textViewRecipe.setText("조리법: " + recipe);

                textViewName.setVisibility(View.VISIBLE);
                textViewMaker.setVisibility(View.VISIBLE);
                textViewRecipe.setVisibility(View.VISIBLE);

                // TTS로 데이터 읽기
                speak("제품명은 " + name + ", 제조사는 " + maker + ", 조리법은 " + recipe);
            }
        } else {
            speak("라면 정보를 가져오지 못했습니다.");
        }
    }

    /**
     * 음성 인식을 시작하는 메서드
     */
    private void startListening() {
        if (speechRecognizer != null) {
            speechRecognizer.startListening(speechRecognizerIntent);
        } else {
            Toast.makeText(this, "음성 인식 초기화에 실패했습니다.", Toast.LENGTH_SHORT).show();
        }
    }

    /**
     * 음성 인식 객체 초기화
     */
    private void initSpeechRecognizer() {
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                Toast.makeText(MainActivity.this, "음성 인식을 시작합니다.", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    handleVoiceCommand(matches.get(0));
                }
            }

            @Override
            public void onEndOfSpeech() {
                Toast.makeText(MainActivity.this, "음성 인식이 종료되었습니다.", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onError(int error) {
                Toast.makeText(MainActivity.this, "음성 인식 오류: " + error, Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onRmsChanged(float rmsdB) {}

            @Override
            public void onBeginningOfSpeech() {}

            @Override
            public void onBufferReceived(byte[] buffer) {}

            @Override
            public void onPartialResults(Bundle partialResults) {}

            @Override
            public void onEvent(int eventType, Bundle params) {}
        });

        // 음성 인식 Intent 설정
        speechRecognizerIntent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        speechRecognizerIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        speechRecognizerIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.KOREAN);
    }

    /**
     * 음성 명령어를 처리하는 메서드
     */
    private void handleVoiceCommand(String command) {
        switch (command) {
            case "조리법":
            case "레시피":
                if (!recipe.isEmpty()) {
                    speak("조리법은 " + recipe);
                } else {
                    speak("조리법 정보를 가져오지 못했습니다.");
                }
                break;
            case "제조사":
            case "브랜드":
                if (!maker.isEmpty()) {
                    speak("제조사는 " + maker);
                } else {
                    speak("제조사 정보를 가져오지 못했습니다.");
                }
                break;
            case "이름":
            case "제품명":
                if (!name.isEmpty()) {
                    speak("이름은 " + name);
                } else {
                    speak("제품명 정보를 가져오지 못했습니다.");
                }
                break;
            case "가격":
            case "얼마":
                if (!price.isEmpty()) {
                    speak("가격은 " + price);
                } else {
                    speak("가격 정보를 가져오지 못했습니다.");
                }
                break;
            default:
                speak("알 수 없는 명령입니다.");
        }
    }

    private void readRamenInfo() {
        // 전체 라면 정보를 읽어주는 메서드
        if (!name.isEmpty() && !maker.isEmpty() && !recipe.isEmpty()) {
            speak("제품명은 " + name + ", 제조사는 " + maker + ", 조리법은 " + recipe);
        } else {
            speak("라면 정보를 가져오지 못했습니다.");
        }
    }

    /**
     * TTS 속도를 조정하는 메서드
     */
    private void adjustTtsSpeed(float delta) {
        ttsSpeed = Math.max(0.5f, Math.min(2.0f, ttsSpeed + delta));
        if (ttsSpeed == 0.5f) {
            speak("TTS 최저 속도");
        } else if (ttsSpeed == 2.0f) {
            speak("TTS 최대 속도");
        } else {
            speak(delta > 0 ? "TTS 빠르게" : "TTS 느리게");
        }
        textToSpeech.setSpeechRate(ttsSpeed);
    }

    /**
     * TTS로 텍스트 읽기
     */
    private void speak(String text) {
        textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
    }

    /**
     * 버튼 클릭 시 진동 제공
     */
    private void vibrate(int duration) {
        if (vibrator != null && vibrator.hasVibrator()) {
            vibrator.vibrate(duration);
        }
    }

    /**
     * TTS 및 음성 인식 객체 해제
     */
    @Override
    protected void onDestroy() {
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        if (speechRecognizer != null) {
            speechRecognizer.destroy();
        }
        super.onDestroy();
    }

    /**
     * NanoHTTPD 서버 클래스
     */
    public class HTTPServer extends NanoHTTPD {
        public HTTPServer(int port) {
            super(port);
        }

        @Override
        public Response serve(IHTTPSession session) {
            if ("/notify".equals(session.getUri())) {
                Log.d("HTTPServer", "알림 요청을 수신했습니다.");
                runOnUiThread(() -> MainActivity.this.speak("물을 다 따랐습니다."));
                return newFixedLengthResponse(Response.Status.OK, "application/json", "{\"status\":\"success\"}");
            }
            return newFixedLengthResponse(Response.Status.NOT_FOUND, "application/json", "{\"status\":\"fail\"}");
        }
    }

    /**
     * 서버 응답 데이터 클래스
     */
    public static class ServerResponse {
        private String status;
        private ProductInfo product_info;

        public String getStatus() {
            return status;
        }

        public ProductInfo getProductInfo() {
            return product_info;
        }
    }

    /**
     * 제품 정보 데이터 클래스
     */
    public static class ProductInfo {
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