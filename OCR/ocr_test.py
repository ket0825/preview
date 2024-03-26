from paddleocr import PaddleOCR

ocr=PaddleOCR(lang="korean")

img_path=r"C:\Users\KHU\Desktop\4학년 1학기\(화,목) 창의적 종합 설계\test.jpg"
result=ocr.ocr(img_path, cls=False)

ocr_result=result[0]
print(ocr_result)