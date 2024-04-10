"""
Temporary used.
"""
import os
import json
import re
from natsort import natsorted

file_ptrn = re.compile(r"_\d+.json$")
same_product_ptrn = re.compile(r"_\d+_\d+.json$")


def ocr_concat():
    dir_name = r"./ocr_jsons"
    output_dir_name = r"./ocr_jsons_processed2"
    if not os.path.exists(output_dir_name):
        os.mkdir(output_dir_name)

    listdir = natsorted(os.listdir(dir_name))
    img_data = []
    product_data = []
    next_count = 1
    for i in range(len(listdir)):
        json_filename = listdir[i]
        json_path = os.path.join(dir_name, json_filename)
        output_path = os.path.join(output_dir_name, json_filename)
        product_name_output_path = same_product_ptrn.sub('.json', output_path)

        with open(json_path, 'r', encoding='utf-8-sig') as json_file:
            ocr_json = json.load(json_file)

        # 마지막 json 파일을 읽기 위함. 다음 것을 항상 체크하는 부분 제거.
        if i == len(listdir)-1:
            # img_data에 리스트가 있다면 연속된 이미지였다는 뜻.
            for item in ocr_json:
                img_data.append(item)     
            json_text_concat = ''
            for line in img_data:
                json_text_concat += line['text'].lower()
            img_data.insert(0, json_text_concat)
            # img_data가 비어있다면 연속된 이미지가 아니었다는 뜻.
            # 마지막으로 이미지 데이터를 넣고 dump.
            product_data.append(img_data)

            with open(product_name_output_path, 'w', encoding='utf-8-sig') as json_file:
                json.dump(product_data, json_file, ensure_ascii=False)

        else:
            # 맨 뒤가 처음이면 다음 것과 concat 해줘야 함.
            next_json_filename = listdir[i+1]
            consecutive_json_filename = json_filename.replace(f'{next_count-1}.json', f'{next_count}.json')           

            # 연속한 경우인 경우.        
            if next_json_filename == consecutive_json_filename:
                for item in ocr_json:
                    img_data.append(item)
                next_count+=1
            # same product라면 그냥 append해준다. 불연속된 이미지여야 하기도 함.
            elif same_product_ptrn.sub("", json_filename) == same_product_ptrn.sub("", next_json_filename):
                # 연속한 경우가 아닌 경우.
                for item in ocr_json:
                    img_data.append(item)     
                json_text_concat = ''
                for line in img_data:
                    json_text_concat += line['text'].lower()
                img_data.insert(0, json_text_concat)
                product_data.append(img_data)
                img_data = []
                next_count = 1
            # same product가 아니라면 json dump 해준다.
            else:
                # img_data가 비어있다면 연속된 이미지가 아니었다는 뜻.
                for item in ocr_json:
                    img_data.append(item)     
                json_text_concat = ''
                for line in img_data:
                    json_text_concat += line['text'].lower()
                img_data.insert(0, json_text_concat)               
                product_data.append(img_data)

                with open(product_name_output_path, 'w', encoding='utf-8-sig') as json_file:
                    json.dump(product_data, json_file, ensure_ascii=False)

                product_data = []
                img_data = []
                next_count = 1  
            

if __name__ == '__main__':
    ocr_concat()

            

            
        

        


