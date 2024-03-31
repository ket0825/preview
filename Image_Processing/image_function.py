from paddleocr import PaddleOCR,draw_ocr
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import shutil
def RGB_extract(image_path):
    image_path=image_path
    img=Image.open(image_path)
    pix=np.array(img)
    print(img.size)

    # 세로 1픽셀마다 가로 픽셀 RGB값 구해서 평균냄 -> 이 값이 가로 한줄 RGB값을 나타낸다고 가정함
    low_pix_mean=[]
    for i in range(img.size[1]):  # 세로픽셀
        low_pix=[]
        for j in range(img.size[0]): #가로 픽셀
            low_pix.append(pix[i][j])
        total_arr=np.array([0,0,0])
        for i in low_pix:
            total_arr+=i
        low_pix_mean.append(list(total_arr/len(low_pix)))
    
    # 가로줄 별 RGB값 리스트 반환
    return low_pix_mean



def slice_image_vertically(image_path, folder_name, gap):
    # 잘린 이미지 저장할 폴더 생성
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # 이미지 로드
    image = Image.open(image_path)
    width = image.size[0]   # 이미지 가로
    height = image.size[1]  # 이미지 세로
    
    # 이미지 잘라서 저장
    for i in range(0, height, gap):
        box = (0, i, width, min(i + gap, height))   # 맨 끝부분
        image_gap = image.crop(box)
        image_gap.save(os.path.join(folder_name, f"{i}.jpg"))


def OCR_image(folder_name, result_folder_name, gap):
    # ocr 결과 사진 저장할 폴더 생성
    result_folder_name = 'result_image'
    if not os.path.exists(result_folder_name):
        os.makedirs(result_folder_name)
    # 문자 OCR
    ocr=PaddleOCR(lang="korean")

    image_list = os.listdir(folder_name)
    image_list = sorted(image_list, key=lambda x: int(''.join(filter(str.isdigit, x))))

    ocr_sequence=[]
    for cnt, image_index in enumerate(image_list):
        image_path=os.path.join(folder_name, image_index)
        # ocr 수행
        result=ocr.ocr(image_path, cls=False)
        
        # print("[최초 ocr 결과]")
        # for line in result[0]:
        #     print(line)

        # ocr 결과 이미지 저장
        image = Image.open(image_path).convert('RGB')
        boxes = [line[0] for line in result[0]]
        txts = [line[1][0] for line in result[0]]
        scores = [line[1][1] for line in result[0]]
        im_show = draw_ocr(image, boxes, txts, scores, font_path='malgun.ttf')
        im_show = Image.fromarray(im_show)
        im_show.save(os.path.join(result_folder_name, image_index))
        
        # print("*"*100)
        
        # 픽셀을 나눠놨기 때문에 result의 바운딩 박스 y좌표에 gap을 더해줘야함
        for line in result[0]:
            for ax in line[0]:
                ax[1]+=gap*cnt
        
        # 텍스트만 뽑히는지
        # print("[텍스트만 뽑히는지 확인]")
        # for line in result[0]:
        #     print(line[1][0])
        
        # y좌표 더해졌는지
        # print("[y좌표 더해졌는지 확인]")
        # for line in result[0]:
        #     print(line)
        
        # 좌표랑 텍스트 튜플로 묶어서 리스트에 저장
        for line in result[0]:
            pair=(line[1][0], line[0])
            ocr_sequence.append(pair)
    


    # 임시로 만들었던 폴더 제거
    if os.path.exists(folder_name):
        for file_name in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        os.rmdir(folder_name)

    # 임시로 만들었던 폴더 제거
    if os.path.exists(result_folder_name):
        for file_name in os.listdir(result_folder_name):
            file_path = os.path.join(result_folder_name, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        os.rmdir(result_folder_name)
    
    # 텍스트랑 좌표 1:1 매칭된 리스트 반환
    return ocr_sequence