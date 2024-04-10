import tkinter.messagebox as msgbox
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import json

current_index = 0
topic_entries = []
topic_frames = []
our_topics = []
file_path = ""


def open_json_file():
    global current_index, data, file_path, our_topics
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])

    if file_path:
        if our_topics and not msgbox.askokcancel('저장 확인', "저장하셔서 다음 것으로 넘어가신다면 확인을 누르세요.\n아니라면 취소를 하고 먼저 저장해주세요."):
            return           

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        current_index = 0
        our_topics = []

        for idx, datum in enumerate(data):
            our_topics.append([{'text': "", "topic": "", 'start_pos': 0, 'end_pos': 0, 'positive_yn': "", 'sentiment_scale':5}])
            if datum.get('our_topics'):
                our_topics[idx] = datum['our_topics']
                
        display_content(data[current_index])
    else:
        data = None
        file_path = None

def display_content(content_data):
    global current_index, topic_entries, our_topics, topic_frames
    scrolled_text.delete('1.0', tk.END)
    scrolled_text.insert(tk.END, content_data['content'])

    # 기존 topic entry 삭제
    for entry in topic_entries:
        for widget in entry:
            widget.destroy()
    for topic_frame in topic_frames:
        topic_frame.destroy()
    topic_entries = []
    topic_frames = []

    # topic entry 새로 생성
    for topic_data in our_topics[current_index]:
        topic_entry = []
        new_frame = create_new_topic_frame()
        new_frame.pack(pady=5)
        topic_frames.append(new_frame)
        topic_text = tk.Text(new_frame, height=2, width=30)
        topic_text.insert(tk.END, topic_data['text'])
        topic_text.pack(side=tk.LEFT, padx=5)
        topic_entry.append(topic_text)

        topic_combobox = ttk.Combobox(new_frame, values=["기능", "발열", "디자인", "포장 상태"], state="normal")
        topic_combobox.set(topic_data['topic'])
        topic_combobox.pack(side=tk.LEFT, padx=5)
        topic_entry.append(topic_combobox)

        positive_yn_combobox = ttk.Combobox(new_frame, width=2, values=["Y", "N"], state="readonly")
        positive_yn_combobox.set(topic_data['positive_yn'])
        positive_yn_combobox.pack(side=tk.LEFT, padx=1)
        topic_entry.append(positive_yn_combobox)

        sentiment_scale_combobox = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(6)], state="readonly")
        sentiment_scale_combobox.set(str(topic_data['sentiment_scale']))
        sentiment_scale_combobox.pack(side=tk.LEFT, padx=1)
        topic_entry.append(sentiment_scale_combobox)

        topic_entries.append(topic_entry)

def save_json_file():
    global current_index, data, file_path, topic_entries, our_topics
    try:
        if data and file_path:
            save_to_our_topics()
            for idx, datum in enumerate(data):
                datum['our_topics'] = our_topics[idx]
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            msgbox.showinfo("저장성공",  "성공적으로 저장되었습니다!")
    except:
        msgbox.showerror("에러","파일 경로나 데이터가 없습니다.")


def next_content():
    global current_index, data, topic_entries, our_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    
    save_to_our_topics()
    current_index = (current_index + 1) % len(data)
    display_content(data[current_index])

def previous_content():
    global current_index, data, topic_entries, our_topics, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    
    save_to_our_topics()
    current_index = (current_index - 1) % len(data)
    display_content(data[current_index])

def add_topic():
    global topic_entries, file_path
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return

    topic_entry = []
    new_frame = create_new_topic_frame()
    new_frame.pack(pady=10)
    topic_frames.append(new_frame)

    topic_text = tk.Text(new_frame, height=2, width=30)
    topic_text.pack(side=tk.LEFT, padx=5)
    topic_entry.append(topic_text)

    topic_combobox = ttk.Combobox(new_frame, values=["기능", "발열", "디자인", "포장 상태"], state="normal")
    topic_combobox.current(0)
    topic_combobox.pack(side=tk.LEFT, padx=5)
    topic_entry.append(topic_combobox)

    positive_yn_combobox = ttk.Combobox(new_frame, width=2, values=["Y", "N"], state="readonly")
    positive_yn_combobox.current(0)
    positive_yn_combobox.pack(side=tk.LEFT, padx=1)
    topic_entry.append(positive_yn_combobox)

    sentiment_scale_combobox = ttk.Combobox(new_frame, width=2, values=[str(i) for i in range(6)], state="readonly")
    sentiment_scale_combobox.current(2)
    sentiment_scale_combobox.pack(side=tk.LEFT, padx=1)
    topic_entry.append(sentiment_scale_combobox)

    topic_entries.append(topic_entry)

def delete_last_topic():
    global topic_entries, file_path
    
    if not file_path:
        msgbox.showerror("에러", "JSON 파일을 열고 진행해주세요.")
        return
    for widget in topic_entries[-1]:        
        widget.destroy()
    
    topic_entries.pop()

    topic_frames[-1].destroy()
    topic_frames.pop()


def create_new_topic_frame():
    return tk.Frame(topic_frame)

def save_to_our_topics():
    global current_index, data, topic_entries, our_topics
    if len(topic_entries) > len(our_topics[current_index]):
        for _ in range(len(topic_entries)-len(our_topics[current_index])): # 추가된 topic만큼 더해줌
            our_topics[current_index].append({'text': "", "topic": "", 'start_pos': 0, 'end_pos': 0, 'positive_yn': "", 'sentiment_scale':5})

    for topic_idx, topic_entry in enumerate(topic_entries):        
        our_topics[current_index]
        for widget_order, widget in enumerate(topic_entry):
            if widget_order == 0:
                # 얘만 text. rstrip으로 끝의 줄바꿈 제거.
                our_topics[current_index][topic_idx]['text'] = widget.get('1.0', tk.END).rstrip() 
                target_str = our_topics[current_index][topic_idx]['text']
                our_topics[current_index][topic_idx]['start_pos'] = data[current_index]['content'].find(target_str)
                our_topics[current_index][topic_idx]['end_pos'] = data[current_index]['content'].find(target_str) + len(target_str)+1 if data[current_index]['content'].find(target_str) > -1 else -1

            elif widget_order == 1:
                our_topics[current_index][topic_idx]['topic'] = widget.get()
            elif widget_order == 2:
                our_topics[current_index][topic_idx]['positive_yn'] = widget.get()
            elif widget_order == 3:
                our_topics[current_index][topic_idx]['sentiment_scale'] = int(widget.get())

root = tk.Tk()
root.title("JSON File Editor")

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
scrolled_text.pack(fill=tk.BOTH, expand=True)


# topic frame.
topic_frame = tk.Frame(root)
topic_frame.pack(ipadx=100, expand=True)

# topic label.
topic_lbl = tk.Label(topic_frame, text="    Text    //  topic   //  감성 긍정/부정  //  감성의 강도")
topic_lbl.pack(side=tk.TOP, pady=5)

# 'Add Topic' 버튼
add_topic_btn = tk.Button(topic_frame, text="Add Topic", command=add_topic)
add_topic_btn.pack(side=tk.LEFT, padx=5)

# 'Delete Last Topic' 버튼
delete_topic_btn = tk.Button(topic_frame, text="Delete Last Topic", command=delete_last_topic)
delete_topic_btn.pack(side=tk.LEFT, padx=8)

root.mainloop()