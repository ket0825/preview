from image_function_main import *

image_path=r"C:\Users\KHU\Desktop\preview\Image_Processing\train_image\로모스 sense8PS Pro 고속 충전 30W 대용량 보조배터리 30000mAh_1.jpg"

# 자를 경계 찾는 함수
cut_pix_list=char_pix_extract(image_path)
# 위에서 찾은 경계로 이미지 다시 잘라서 last_image폴더에 저장하는 함수
last_image_cut(image_path,"last_image",cut_pix_list)
# last_image 폴더에 저장된 이미지 ocr한 후에, 문자+바운딩박스 튜플로 묶어서 하나의 리스트로 반환하는 함수
print(last_OCR_image("last_image",cut_pix_list))