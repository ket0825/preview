from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import shutil
ocr = PaddleOCR(lang="korean")

def slice_image_vertically(image_path, folder_name, gap):
    # 잘린 이미지 저장할 폴더 생성
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # 이미지 로드
    image = Image.open(image_path)
    width = image.size[0]   # 이미지 가로
    height = image.size[1]  # 이미지 세로
    
    cuted_pix=[]
    # 이미지 잘라서 저장
    for i in range(0, height, gap):
        box = (0, i, width, min(i + gap, height))   # 맨 끝부분
        cuted_pix.append(min(i + gap, height))
        image_gap = image.crop(box)
        image_gap.save(os.path.join(folder_name, f"{i}.jpg"))
    
    return height # 높이값 반환


def OCR_image(folder_name, gap):

    image_list = os.listdir(folder_name)
    image_list = sorted(image_list, key=lambda x: int(''.join(filter(str.isdigit, x))))

    # 텍스트랑 좌표 1:1로 매칭시켜서 넣을 리스트
    ocr_sequence=[]
    for cnt, image_index in enumerate(image_list):
        image_path=os.path.join(folder_name, image_index)
        # ocr 수행
        result=ocr.ocr(image_path, cls=False)
        
        # 픽셀을 나눠놨기 때문에 result의 바운딩 박스 y좌표에 gap을 더해줘야함
        for line in result[0]:
            for ax in line[0]:
                ax[1]+=gap*cnt
        # 바운딩박스 좌표랑 문자를 튜플로 묶어서 리스트에 추가
        for line in result[0]:
            pair=(line[1][0], line[0])
            ocr_sequence.append(pair)

    # 이미지 잘라서 넣었던 폴더 제거
    if os.path.exists(folder_name):
        for file_name in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    return ocr_sequence     #바운딩 박스 좌표랑 문자가 튜플로 묶인 리스트 반환


# 이분탐색
def find_small_largest(arr, target):
    left = 0
    right = len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return arr[mid]
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    # while문끝나고 났을때 right가 더 작은 값이 되어있음
    if(arr[right]<target):
        return arr[right]
    else:
        return arr[right-1]
    


# 이미지 자를 임계값 픽셀 찾기
def char_pix_extract(image_path):
    image_path=image_path
    height = slice_image_vertically(image_path, 'image', 2000)
    result=OCR_image('image', 2000)
    boundary=[]
    cut_candidate=set()
    for bounding_box in result:
        top= int(min([bounding_box[1][i][1] for i in range(4)]))
        bottom=int(max([bounding_box[1][i][1] for i in range(4)]))
        boundary.append((top,bottom))   # 문자 있는 구간 위아래 기준

        for i in range(10):
            cut_candidate.add(top-i)
            cut_candidate.add(bottom+i)

    # 문자 구간사이에 들어가는 후보 제거
    to_remove = set()
    for candidate in cut_candidate:
        for pair in boundary:
            if candidate > pair[0] and candidate < pair[1]:
                to_remove.add(candidate)

    for candidate in to_remove:
        cut_candidate.remove(candidate)
    cut_candidate = sorted(list(cut_candidate))
    
    result_pix = [0]
    print("이미지 길이:", height)
    if(height<2000):
        return [0, height]
    cut_line = 2000
    # print("후보:", cut_candidate)
    while cut_line < height:
        new_cut = find_small_largest(cut_candidate, cut_line)
        # 새롭게 찾은게 기준선보다 크거나 같으면, 기준선으로 넣어줘야함
        if new_cut >= cut_line:
            result_pix.append(cut_line)
            cut_line = cut_line+2000
        
        # 새롭게 찾은게 기준선보다 작으면
        else:
            # 만약 진짜 처음 나온 선이면
            if (new_cut not in result_pix):
                result_pix.append(new_cut)
                cut_line = new_cut + 2000
            # 이미 있었던 선이면
            else:
                result_pix.append(cut_line)
                cut_line+=2000
    result_pix.append(height) # 맨 마지막 픽셀 (height) 넣어주기
        

    return result_pix


# 찾은 임계값 기준으로 이미지 자르기
def last_image_cut(image_path, folder_name, cut_pix_list):
    # 잘린 이미지 저장할 폴더 생성
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # 이미지 로드
    image = Image.open(image_path)
    width = image.size[0]   # 이미지 가로
    
    for i in range(len(cut_pix_list)-1):
        box = (0, cut_pix_list[i], width, cut_pix_list[i+1])
        croped_image = image.crop(box)
        croped_image.save(os.path.join(folder_name, f"{i}.jpg"))


def last_OCR_image(folder_name, cut_pix_list):

    image_list = os.listdir(folder_name)
    # 이미지 잘린 순서대로 정렬
    image_list = sorted(image_list, key=lambda x: int(''.join(filter(str.isdigit, x))))

    # 텍스트랑 좌표 1:1로 매칭시켜서 넣을 리스트
    ocr_sequence=[]
    for image_index, cut_line in zip(image_list, cut_pix_list[:-1]):
        image_path=os.path.join(folder_name, image_index)
        # ocr 수행
        result=ocr.ocr(image_path, cls=False)
        
        # 픽셀을 나눠놨기 때문에 result의 바운딩 박스 y좌표에 자른 경계선 픽셀값을 더해줘야함
        for line in result[0]:
            for ax in line[0]:
                ax[1]+=cut_line
        # 바운딩박스 좌표랑 문자를 튜플로 묶어서 리스트에 추가
        for line in result[0]:
            pair=(line[1][0], line[0])
            ocr_sequence.append(pair)

    # 이미지 잘라서 넣었던 폴더 제거
    if os.path.exists(folder_name):
        for file_name in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    return ocr_sequence     #바운딩 박스 좌표랑 문자가 튜플로 묶인 리스트 반환