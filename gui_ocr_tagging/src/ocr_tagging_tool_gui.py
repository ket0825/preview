import tkinter.messagebox as msgbox
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import json

current_index = 0
topic_entries = []
topic_frames = []
ocr_topics = []
file_path = ""
data_len = 0


def open_json_file():
    global current_index, data, file_path, ocr_topics, data_len
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])

    if file_path:
        if ocr_topics and not msgbox.askokcancel('저장 확인', "저장하셔서 다음 것으로 넘어가신다면 확인을 누르세요\n아니라면 취소를 하고 먼저 저장해주세요"):
            return           
        path_text.config(state='normal')  # 편집 가능하게 변경
        path_text.delete(1.0, tk.END)    
        path_text.insert(tk.END, file_path) 
        path_text.config(state='disabled') # 넣었으니 편집 불가능.

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        current_index = 0
        ocr_topics = []
        data_len = len(data)
        for idx in range(len(data)):
            ocr_topics.append([])
            # 이미 토픽이 존재한다면 (1번째임)
            if isinstance(data[idx][1], list):
                topics = data[idx][1]
                for topic in topics:
                    # topic이 유의미 하지 않다면 pass.
                    if (topic['text'] == "" 
                        or topic['topic'] == "" 
                        or topic['start_pos'] == -1 
                        or topic['end_pos'] == -1
                        ):
                        continue
                    # 생성된 ocr_topics에 넣어줌.
                    ocr_topics[idx].append(topic)
            else:
                # 생성된 ocr_topics에 디폴트로 넣어줌.
                ocr_topics[idx].append({'text': "", "topic": "", 'start_pos': 0, 'end_pos': 0})
        
        display_content(data[current_index])
    else:
        data = None
        file_path = None

def modify_page_index():
    global current_index, data_len 
    page_index_lbl.config(text=f"{current_index+1} / {len(data)}")

def display_content(ocr_data):
    global current_index, topic_entries, ocr_topics, topic_frames
    scrolled_text.config(state='normal')
    scrolled_text.delete('1.0', tk.END)
    scrolled_text.insert(tk.END, ocr_data[0]) # ocr 모두 이어붙인 것.
    scrolled_text.config(state='disabled')
    modify_page_index()
    # 기존 topic entry 삭제
    for entry in topic_entries:
        for widget in entry:
            widget.destroy()
    for topic_frame in topic_frames:
        topic_frame.destroy()
    topic_entries = []
    topic_frames = []

    # topic entry 새로 생성
    for topic_data in ocr_topics[current_index]:
        topic_entry = []
        new_frame = create_new_topic_frame()
        new_frame.pack(pady=5)
        topic_frames.append(new_frame)

        topic_text = tk.Text(new_frame, height=2, width=30)
        topic_text.insert(tk.END, topic_data['text'])
        topic_text.config(font=('Times New Roman', 12))
        topic_text.pack(side=tk.LEFT, padx=5)
        topic_entry.append(topic_text)

        topic_combobox = ttk.Combobox(new_frame, values=["기능", "발열", "디자인", "포장 상태"], state="normal")
        topic_combobox.set(topic_data['topic'])
        topic_combobox.pack(side=tk.LEFT, padx=5)
        topic_entry.append(topic_combobox)

        topic_entries.append(topic_entry)

def save_json_file():
    global current_index, data, file_path, topic_entries, ocr_topics
    try:
        if data > 0 and file_path:
            save_to_ocr_topics()

            # clean ocr_topics
            to_topic_delete = ocr_topics.copy()
            for idx, topics in enumerate(to_topic_delete):
                for idx_topic, topic in enumerate(topics):
                    if (topic['text'] == "" 
                        or topic['topic'] == "" 
                        or topic['start_pos'] == -1 
                        or topic['end_pos'] == -1
                        ):
                        ocr_topics[idx].pop(idx_topic)
            for idx, datum in enumerate(data):
                # 존재해야만 한다.
                if (isinstance(ocr_topics[idx], list) # list 형태이고
                    and ocr_topics[idx]): # 빈 리스트가 아니라면.
                    datum[1] = ocr_topics[idx]
                else:
                    if ocr_topics[idx]: # 빈 리스트가 아니라면.
                        datum.insert(1, ocr_topics[idx])

            with open(file_path, 'w', encoding='utf-8-sig') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            msgbox.showinfo("저장성공",  "성공적으로 저장되었습니다!")
        else:
            msgbox.showerror("에러","데이터가 없습니다. 저장에 실패했어요")    
    except:
        msgbox.showerror("에러","파일 경로나 데이터가 없습니다")


def next_content():
    global current_index, data, topic_entries, ocr_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요")
        return
    
    save_to_ocr_topics()

    if current_index+1 == len(data):
        msgbox.showwarning("주의", "현재 페이지가 마지막입니다")
        return
    current_index+=1
    display_content(data[current_index])

def previous_content():
    global current_index, data, topic_entries, ocr_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요")
        return
        
    save_to_ocr_topics()

    if current_index == 0:
        msgbox.showwarning("주의", "현재 페이지가 처음입니다")
        return
    current_index-=1
    display_content(data[current_index])

def add_topic():
    global topic_entries, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요")
        return

    topic_entry = []
    new_frame = create_new_topic_frame()
    new_frame.pack(pady=10)
    topic_frames.append(new_frame)

    topic_text = tk.Text(new_frame, height=2, width=40)
    topic_text.pack(side=tk.LEFT, padx=5)
    topic_text.config(font=('Times New Roman', 12))
    topic_entry.append(topic_text)

    topic_combobox = ttk.Combobox(new_frame, values=["기능", "발열", "디자인", "포장 상태"], state="normal")
    topic_combobox.pack(side=tk.LEFT, padx=5)
    topic_entry.append(topic_combobox)

    topic_entries.append(topic_entry)

def delete_last_topic():
    global topic_entries, file_path
    
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요")
        return
    elif not topic_entries:
        msgbox.showerror("에러", "지울 topic이 없습니다")
        return

    
    for widget in topic_entries[-1]:        
        widget.destroy()
    
    topic_entries.pop()

    topic_frames[-1].destroy()
    topic_frames.pop()


def create_new_topic_frame():
    return tk.Frame(topic_frame)

def save_to_ocr_topics():
    global current_index, data, topic_entries, ocr_topics
    if len(topic_entries) > len(ocr_topics[current_index]):
        for _ in range(len(topic_entries)-len(ocr_topics[current_index])): # 추가된 topic만큼 더해줌
            ocr_topics[current_index].append({'text': "", "topic": "", 'start_pos': 0, 'end_pos': 0})

    for topic_idx, topic_entry in enumerate(topic_entries):        
        for widget_order, widget in enumerate(topic_entry):
            if widget_order == 0:
                # 얘만 text. rstrip으로 끝의 줄바꿈 제거.
                ocr_topics[current_index][topic_idx]['text'] = widget.get('1.0', tk.END).rstrip() 
                target_str = ocr_topics[current_index][topic_idx]['text']
                ocr_topics[current_index][topic_idx]['start_pos'] = data[current_index][0].find(target_str)
                ocr_topics[current_index][topic_idx]['end_pos'] = data[current_index][0].find(target_str) + len(target_str)+1 if data[current_index][0].find(target_str) > -1 else -1
            elif widget_order == 1:
                ocr_topics[current_index][topic_idx]['topic'] = widget.get()


root = tk.Tk()
root.title("JSON File Editor")

# 경로 프레임.
path_frame = tk.Frame(root)
path_frame.pack(pady=10)

# 경로 레이블.
path_lbl = tk.Label(path_frame, text='Path: ')
path_lbl.config(font=('Times New Roman', 12))
path_lbl.pack(side=tk.LEFT, pady=10, padx=5)

# 경로 텍스트.
path_text = tk.Text(path_frame, state='disabled', height=2, width=80)
path_text.config(font=('Times New Roman', 12))
path_text.pack(fill=tk.BOTH, pady=10)

# 버튼 프레임
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

# ScrolledText 프레임
text_frame = tk.Frame(root)
text_frame.pack(fill=tk.BOTH, expand=True)

# 'Open' 버튼
open_btn = tk.Button(btn_frame, text="Open", command=open_json_file)
open_btn.pack(side=tk.LEFT, padx=5)

# 'Save' 버튼
save_btn = tk.Button(btn_frame, text="Save", command=save_json_file)
save_btn.pack(side=tk.LEFT, padx=5)

# 'Next' 버튼
next_btn = tk.Button(btn_frame, text="Next", command=next_content)
next_btn.pack(side=tk.LEFT, padx=5)

# 'Previous' 버튼
prev_btn = tk.Button(btn_frame, text="Previous", command=previous_content)
prev_btn.pack(side=tk.LEFT, padx=5)

# ScrolledText 위젯
scrolled_text = scrolledtext.ScrolledText(text_frame, width=80, height=20)
scrolled_text.config(font=('Times New Roman', 14))
scrolled_text.pack(fill=tk.BOTH, expand=True)

# topic frame.
topic_frame = tk.Frame(root)
topic_frame.pack(ipadx=100, expand=True)

# topic label.
topic_lbl = tk.Label(topic_frame, text="    Text    //    topic    ")
topic_lbl.config(font=('Times New Roman', 14))
topic_lbl.pack(side=tk.TOP, pady=5)

# 'Add Topic' 버튼
add_topic_btn = tk.Button(topic_frame, text="Add Topic", command=add_topic)
add_topic_btn.pack(side=tk.LEFT, padx=5)

# 'Delete Last Topic' 버튼
delete_topic_btn = tk.Button(topic_frame, text="Delete Last Topic", command=delete_last_topic)
delete_topic_btn.pack(side=tk.LEFT, padx=8)

# 페이지 index frame.
page_index_frame = tk.Frame(root)
page_index_frame.pack(side=tk.BOTTOM, pady=5)

# 페이지 index label.
page_index_lbl = tk.Label(page_index_frame)
page_index_lbl.config(font=('Times New Roman', 14))
page_index_lbl.pack(fill=tk.BOTH)

root.mainloop()