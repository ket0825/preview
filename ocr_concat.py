import os
import json
import re
from natsort import natsorted

file_ptrn = re.compile(r"_\d+.json$")



def ocr_concat():
    dir_name = r"./ocr_jsons"
    output_dir_name = r"./ocr_jsons_processed"
    if not os.path.exists(output_dir_name):
        os.mkdir(output_dir_name)

    listdir = natsorted(os.listdir(dir_name))
    data = []
    next_count = 1
    for i in range(len(listdir) - 1):
        json_filename = listdir[i]
        json_path = os.path.join(dir_name, json_filename)
        output_path = os.path.join(output_dir_name, json_filename)
        processed_output_path = file_ptrn.sub('.json', output_path)
        
        # 맨 뒤 1이면 다음 것과 concat 해줘야 함.
        next_json_filename = listdir[i+1]
        consecutive_json_filename = json_filename.replace(f'{next_count-1}.json', f'{next_count}.json')
        with open(json_path, 'r', encoding='utf-8-sig') as json_file:
            ocr_json = json.load(json_file)     
        
        # 연속한 경우인 경우.        
        if next_json_filename == consecutive_json_filename:
            for item in ocr_json:
                data.append(item)
            next_count+=1
            continue
        
        # 연속한 경우가 아닌 경우.
        for item in ocr_json:
            data.append(item)     
        json_text_concat = ''
        for line in data:
            json_text_concat += line['text'].lower()
        data.insert(0, json_text_concat)

        with open(processed_output_path, 'w', encoding='utf-8-sig') as json_file:
            json.dump(data, json_file, ensure_ascii=False)
            
        data.clear()
        next_count = 1


if __name__ == '__main__':
    ocr_concat()

            

            
        

        


