from paddleocr import PaddleOCR
import time

ocr=PaddleOCR(lang="korean")

t1 = time.time()
img_path=r"./full_img.png"
result=ocr.ocr(img_path, cls=False)

ocr_result=result[0]

with open('test_ocr.txt','w',encoding='utf-8-sig') as f:
    f.write(ocr_result)

t2 = time.time()

print(f"소요 시간: {(t2-t1):2f}")
