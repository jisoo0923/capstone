
// 카메라 촬영 후 결과 처리
@Override
protected void onActivityResult(int requestCode, int resultCode, Intent data) {
    super.onActivityResult(requestCode, resultCode, data);

    if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
        if (data != null && data.getExtras() != null) {
            Bitmap imageBitmap = (Bitmap) data.getExtras().get("data");
            capturedImage = imageBitmap;  // capturedImage에 저장
            imageView.setImageBitmap(imageBitmap);  // ImageView에 표시

            // 사진을 찍은 후 서버에 자동으로 업로드
            uploadImageToServer(imageBitmap);
        }
    }
}
