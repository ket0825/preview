# 태그 매치
"""https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
# XPATH 예시들.
"""https://selenium-python.readthedocs.io/locating-elements.html"""

# TODO: ip banned case.
# TODO: crawled at the last review...

#stdlib
import json
import time
import random
import datetime
import re
import os
from shutil import rmtree
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor

import multiprocessing as mp
import traceback

from queue import Empty, Full

from functools import partial
from typing import Dict, Any


# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
# from paddleocr import PaddleOCR

# custom lib.
from log import Logger 
from image_processing.image_function_main import char_pix_extract, make_ocr_sequence, make_ocr_dict
from route_handler.route_handler import RouteHandler
from image_processing.ocr_engine import OCREngine



log = Logger.get_instance()
route_handler = RouteHandler()
double_space_ptrn = re.compile(r" {2,}")
double_newline_ptrn = re.compile(r"\n{2,}")
access_word_ptrn = re.compile(r"[^가-힣ㄱ-ㅎㅏ-ㅣ0-9a-zA-Z\s'\"@_#$\^&*\(\)\-=+<>\/\|}{~:…℃±·°※￦\[\]÷\\;,\s]")
executor = ThreadPoolExecutor(max_workers=8)

def get_links(path:str) -> list:
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        product_raw_json = json.load(json_file)
        links = [item['url'] for item in product_raw_json['items']]
        product_names = [item['name'] for item in product_raw_json['items']]
        category = product_raw_json['category']
        match_nv_mids = [item['match_nv_mid'] for item in product_raw_json['items']]
        return links, product_names, category, match_nv_mids


def ocr_function(src: str, ocr_idx_queue) -> Dict:
    try:
        cut_pix_list = char_pix_extract(src, ocr_idx_queue)  # 몇 개를 해야 할지 나옴.
        # 그러면 그 수에 맞춰서 OCR을 해야 함.           
        # TODO: multiprocessing.                    
        return make_ocr_sequence(src, cut_pix_list, ocr_idx_queue, width_threshold=150, height_threshold=100)
    except Exception as e:
        log.warning(f"[WARNING] OCR failed. {e}")
        return {}
    
def char_pix_extract_wrapper(img_ocr_list: list) -> list:        
    # is_empty = False    
    # while char_pixel_task_queue.qsize() > 0:  # 다중 프로세스에서는 신뢰할 수 없다고 함.      
    try:
        ocr_engine = OCREngine.factory(0)
    except Exception as e:
        log.warning(f"[WARNING] OCR Engine failed. {e}")
        return
        
    char_pix_results = []
    
    for img_ord, img_src in img_ocr_list:
        res = char_pix_extract(img_src, ocr_engine)        
        for i in range(len(res)-1):
            cut_pix_tuple = (res[i], res[i+1])
            char_pix_results.append({
                "src": img_src,
                "img_ord": img_ord,
                "cut_ord": i,
                "cut_pix_tuple": cut_pix_tuple
            })
            
    return char_pix_results
        
        
    
def make_ocr_sequence_wrapper(char_pix_result: list) -> list:
    ocr_engine = OCREngine.factory(0)
    ocr_task_results = []            

    for char_pix_dict in char_pix_result:
        img_ord = char_pix_dict['img_ord']
        src = char_pix_dict['src']
        cut_pix_tuple = char_pix_dict['cut_pix_tuple']
        cut_ord = char_pix_dict['cut_ord']
        res = make_ocr_dict(src, cut_pix_tuple, ocr_engine, width_threshold=150, height_threshold=100)
        if not res:
            res = {
                'img_str': "",
                'bbox_text': [],
            }
                        
        ocr_task_results.append({
                "cut_ord": cut_ord,
                "img_ord": img_ord,
                "ocr_result": res
            })   
        
    return ocr_task_results         
    
            
def make_ocr_sequence_worker(ocr_task_queue:mp.Queue, ocr_task_results_queue:mp.Queue) -> None:            
    """_summary_

    Args:
        ocr_task_queue (mp.Queue): inside: {
                        "src": src,
                        "img_ord": img_ord,
                        "cut_pix_tuple": res
                    }        
        ocr_task_results_queue (mp.Queue): inside: {
                        "cut_ord": cut_ord,
                        "img_ord": img_ord,
                        "ocr_result": res
                    }
    """
    # is_empty = False
    # while ocr_task_queue.qsize() > 0:  # 다중 프로세스에서는 신뢰할 수 없다고 함.      
    try:
        ocr_engine = OCREngine.factory(0)
    except Exception as e:
        log.warning(f"[WARNING] OCR Engine failed. {e}")
        return        

    while True:                
        try:            
            task_dict = ocr_task_queue.get(timeout=1)  # timeout을 줘야 함. Empty가 발생할 수 있음.
            
            img_ord = task_dict['img_ord']
            src = task_dict['src']
            cut_pix_tuple = task_dict['cut_pix_tuple']
            cut_ord = task_dict['cut_ord']        
            
            print(f"img_ord: {img_ord}, cut_ord: {cut_ord}")
                
            res = make_ocr_dict(src, cut_pix_tuple, ocr_engine, width_threshold=150, height_threshold=100)            
            if not res:
                res = {
                    'img_str': "",
                    'bbox_text': [],
                }
            
            if isinstance(res, str) and res == "Failed":
                log.info(f"[INFO] OCR failed. Retry...")
                ocr_task_queue.put(task_dict)
            else:
                ocr_task_results_queue.put({
                        "cut_ord": cut_ord,
                        "img_ord": img_ord,
                        "ocr_result": res
                    })  
                         
        except Empty:
            # is_empty = True            
            break    
            
        except Exception as e:
            log.warning(f"[WARNING] OCR failed. {e}")
            ocr_task_queue.put(task_dict)                
            continue
    
    del ocr_engine
    print("OCR Sequence Done.")
    return
        
    
    
    
    

def fetch_product_detail(driver: Driver):
    top_info = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'top_info_inner_')]")[0]
    top_cells = top_info.find_elements(By.XPATH, ".//span[contains(@class, 'top_cell_')]")    
    
    brand = ""
    maker = ""
    grade = -1
    name = "",
    lowest_price = -1,

    for cell in top_cells:
        if '브랜드' not in cell.text and '제조사' not in cell.text:
            continue
        if '브랜드' in cell.text and '카탈로그' not in cell.text:
            brand = cell.text.replace("브랜드","").replace(" ","")
        elif '제조사' in cell.text:
            maker = cell.text.replace("제조사","").replace(" ","")
    
    # Get grade 
    try:
        grade = driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'top_grade_')]").text
        grade = float(grade.replace("평점", ""))
    except:
        pass
    
    # Get name
    try:
        name = driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'top_summary_title_')]/h2").text
    except:
        pass

    try:
        lowest_price = driver.driver.find_element(By.XPATH, ".//em[contains(@class, 'lowestPrice_num_')]").text
        lowest_price = lowest_price.replace(",", "").replace("원", "")
    except:
        pass

    return brand, maker, grade, name, lowest_price

def is_banned(naver_shopping_driver:Driver) :
    # IP Blocked 시, floating tab이 안나옴. 이걸로 체크.
    try:
        floating_tabs = naver_shopping_driver.wait_until_by_xpath(10, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        return False
    except:
        if naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'content_error')]"):
            log.warning("[WARNING] IP Blocked.")
            # 이후 proxy ip 바꿔서 naver_shopping_driver 다시 얻어야 함.
            naver_shopping_driver.set_ip_dirty()
            naver_shopping_driver.get_current_url()
            return True


def fetch_spec(driver:Driver):    
    top_more = driver.driver.find_element(By.XPATH, ".//a[contains(@class, 'top_more_')]")
    driver.move_to_element(top_more)
    top_more.click() # 더 보기 클릭.
    
    spec_dict = {}
    time.sleep(2)
    tables = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'attribute_product_attribute_')]/table")
    for table in tables:
        table_rows = table.find_elements(By.XPATH, ".//tr")
        for row in table_rows:
            keys = row.find_elements(By.XPATH, ".//th")
            vals = row.find_elements(By.XPATH, ".//td")
            for key, val in zip(keys, vals):
                spec_dict[key.text] = val.text

    return spec_dict


def get_image_specs(driver:Driver, xpath, max_ocr_workers=3):
    """
    Get image specs with xpath.
    
    max_ocr_workers: int (default=4)
    Get ocr_idx_queue and put the images in the queue.
    char_pix_extract: this should be done first.
    
    
    ------------
    return
    image_urls: list[str] / src list
    seller_spec: list[Dict] / ocr results

    
    
    """
    # multiprocessing 한계: 여러 개의 프로세스에서 Queue로 공유할 수 있으려면 pickleable 해야 함. PaddleOCR은 그렇지 않음.
    
    time.sleep(3)
    web_elements = driver.driver.find_elements(By.XPATH, xpath)
    # wait_located_list_until_by_xpath을 사용하면 없는 경우에 exception을 발생시켜 문제가 발생함.
    
    image_urls = [] # img_urls
    seller_spec = []
    
    
    for web_element in web_elements:
        src = web_element.get_attribute('src')
        image_urls.append(src)                    
        driver.move_to_element(web_element)
        time.sleep(0.5)
    
    # .gif, 동영상 등의 확장자를 막기 위함.
    img_ocr_list = [(img_ord, image_url) for img_ord, image_url in enumerate(image_urls) if '.jpg' in image_url or '.png' in image_url or ".jpeg" in image_url]  # ocr queue에 넣을 이미지 리스트.        
    
    if not img_ocr_list:
        log.info(f"[WARNING] There is no image to OCR.")
        return [], []
    

    char_pix_result = char_pix_extract_wrapper(img_ocr_list) # queue 작업 취소함. 
    # 이유 1. OCR engine init 시간이 더 오래 걸림.
    # 이유 2. Mananger를 사용하여 이 또한 복사가 됨.
    ocr_result = []
    
    # 여기서 ocr queue를 진행해야 함.    
    process_count = min(max_ocr_workers, len(char_pix_result))
    processes = []
    
    if process_count > 2:          
        # ocr_queue_manager = mp.Manager()    # Manager()를 통해 Queue를 만듦 (공유 메모리를 위함. 따로 프로세스를 하나 더 만들고, 이걸로 관리함(spawn으로 만드는 듯). 이래야 Join 시에 deadlock 발생하지 않음.)    ocr_task_queue = ocr_queue_manager.Queue()  # task_list
        # ocr_task_queue = ocr_queue_manager.Queue()  # task_list
        # ocr_task_results_queue = ocr_queue_manager.Queue()  # result_list        
        ocr_task_queue = mp.Queue()  # task_list
        ocr_task_results_queue = mp.Queue()  # result_list        
                
        for char_pix_result in char_pix_result:
            ocr_task_queue.put(char_pix_result)
                
        for _ in range(process_count):
            p = mp.Process(target=make_ocr_sequence_worker, args=(ocr_task_queue, ocr_task_results_queue)) # 핵심은 결국 queue 내부를 모두 소비해야 함. 소비는 아래 get에서 진행함.
            p.start()
            processes.append(p)
        
        # polling 방식으로 queue를 확인함.
        while any(p.is_alive() for p in processes):
            try:
                ocr_result.append(ocr_task_results_queue.get(timeout=1))                 
            except Empty:
                continue
            
        
        for p in processes:        
            p.join()    
        
        print("OCR process joined")                           
        
        ocr_result.sort(key=lambda x: (x['img_ord'], x['cut_ord']))        
    else:    
        ocr_result = make_ocr_sequence_wrapper(char_pix_result)        
    
    seller_spec = [elem['ocr_result'] for elem in ocr_result ]
    log.info(f"[INFO] seller_spec: {seller_spec}")
    return seller_spec, image_urls

# TODO: later, it should be an mp.
def get_product_spec(driver:Driver, max_ocr_workers=4):
    try:
        # 제품정보 섹션 찾기
        spec_info_section = driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")    
        driver.move_to_element(element=spec_info_section)
    except:
        log.info(f"[WARNING] There is no product sections.")
        return {}, [], []

    # html tag에 height가 있는데...?
    naver_spec =  {} 
    seller_spec =  []
    img_urls = []
    
    # 본 컨텐츠는 ...에서 제공받은 정보입니다. 부분
    try:
        driver.wait_until_by_xpath(5, ".//p[contains(@class, 'imageSpecInfo_provide_')]")
    except:
        try:
            driver.wait_until_by_xpath(5, ".//p[contains(@class, 'specInfo_provide_')]") # 이미지 스펙 없는 경우.
        except TimeoutException:
            log.info(f"[WARNING] There is no product details.")    

    # 일반적인 테이블 스펙 추출 가능한지 확인.
    try:
        driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'imageSpecInfo_export_')]")
    except:
        # 안되면 naver spec.
        log.info(f"[INFO] No export spec at here.")
        try:
            tables = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'attribute_product_attribute_')]/table")
            for table in tables:
                table_rows = table.find_elements(By.XPATH, ".//tr")
                for row in table_rows:
                    keys = row.find_elements(By.XPATH, ".//th")
                    vals = row.find_elements(By.XPATH, ".//td")
                    for key, val in zip(keys, vals):
                        naver_spec[key.text] = {
                                            'text': val.text, 
                                            'location': [val.location['y'], val.location['x']]
                                            }
        except:
            log.info(f"[WARNING] There is no product tables.")
                
    try:
        seller_spec_payload, img_urls_payload = get_image_specs(driver, ".//p[contains(@id, 'detailFromBrand')]/img", max_ocr_workers=max_ocr_workers)
        if not seller_spec_payload:
            seller_spec_payload, img_urls_payload = get_image_specs(driver, ".//div[contains(@class, 'imageSpecInfo_product_img_')]//img", max_ocr_workers=max_ocr_workers)

        seller_spec.extend(seller_spec_payload)
        img_urls.extend(img_urls_payload)        
    except NoSuchElementException:        
        log.warning(f"[WARNING] There is no image seller_specs.")
        
    return naver_spec, seller_spec, img_urls

def review_formatter(reviews:list[dict]) -> None:
    # remain_key = ['id', 'content', 'aidaModifyTime', 'mallId', 'mallSeq', 'matchNvMid', 'qualityScore', 'starScore', 'topicCount', "topicYn", 'topics', 'userId', 'mallName']    
    keys_to_remove = ["aidaCreateTime", "esModifyTime", "modifyDate", "pageUrl", "registerDate", "imageCount", "imageYn", "images", "mallProductId", "mallReviewId", "rankScore", "title", "videoCount", "videoYn", "videos", "mallLogoUrl"]        
    # topics 관련 제거 예정 .
    
    for review in reviews:        
        for key in keys_to_remove:
            review.pop(key)                
        # review['content'] = review['content'].replace('<br>', '\n')\
        #                                     .replace('<br/>', '\n')\
        #                                     .replace("\r\n", "\n")\
        #                                     .replace("\r", "\n")                            
        # review['content'] = BeautifulSoup(review['content'], 'lxml').text
        # review['content'] = access_word_ptrn.sub("", review['content'])
        # review['content'] = double_space_ptrn.sub(" ", review['content'])
        # review['content'] = double_newline_ptrn.sub("\n", review['content'])
        # review['content'] = review['content'].strip()
        
        # same as above.
        review['content'] = double_newline_ptrn.sub(
            "\n", double_space_ptrn.sub(
                " ", access_word_ptrn.sub(
                    "", BeautifulSoup(
                        review['content'].replace('<br>', '\n')\
                                            .replace('<br/>', '\n')\
                                            .replace("\r\n", "\n")\
                                            .replace("\r", "\n"), 
                                        'lxml').text)
                ).strip())
        

def log_filter(log_):
    return (
        # is an actual response
        log_["method"] == "Network.responseReceived"
        # and json
        and "json" in log_["params"]["response"]["mimeType"]
    )
    
global total_reviews
total_reviews = []

def clear_callback(future):
    global total_reviews
    try:
        res_text, res_code = future.result()
        log.info(f"Response: {res_text}, Code: {res_code}")
        total_reviews.clear()  # 작업 완료 후 clear
    except Exception as e:
        log.error(f"Error in callback: {e}")
    

def upsert_review(
    naver_shopping_driver: Driver, 
    prid:str, 
    match_nv_mid:str, 
    s_category:str, 
    type:str="R0", 
    for_local_test=True
    ) -> Dict[str, Any]:
    """
    Flush log buffer and upsert reviews.
    """
    # Get review log
    chrome_logs_raw = naver_shopping_driver.driver.get_log("performance")
    chrome_logs = [json.loads(lr["message"])["message"] for lr in chrome_logs_raw]
    global total_reviews
    
    for log_ in filter(log_filter, chrome_logs):
        request_id = log_["params"]["requestId"]
        resp_url = log_["params"]["response"]["url"]
        if '/api/review' in resp_url:    
            # review url 구조:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
            log.info(f"Caught {resp_url}")        
            reviews = json.loads(naver_shopping_driver.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body'])['reviews']
            review_formatter(reviews)
            
            ids_to_time = {
                review['id']: review['aidaModifyTime']
                for review in reviews
            }    
            
            accept_ids = route_handler.check_if_need_update(ids_to_time)
            log.info(f"accept_ids: {accept_ids}")
            reviews = [review for review in reviews if review['id'] in accept_ids]
            if reviews:
                log.info(f"reviews[0]: {reviews[0]}")
            total_reviews.extend(reviews)

    
    
    # Complete review formatting.
    # post request to db.
    
    if len(total_reviews) >= 5:
                
        payload = {
            'type': type,
            'category': s_category,
            'prid': prid,
            'match_nv_mid': match_nv_mid,
            'reviews': total_reviews
        }                
        current_time = datetime.datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss")
        global start_date, json_save_fp
        if for_local_test:
            if not os.path.exists(f"./{json_save_fp}/{start_date}_{s_category}_review"):
                os.makedirs(f"./{json_save_fp}/{start_date}_{s_category}_review")
            with open(f"./{json_save_fp}/{start_date}_{s_category}_review/{current_time}_{prid}.json", 'w', encoding='utf-8-sig') as json_file:                                                         
                json.dump(payload, json_file, ensure_ascii=False, indent=4)    
            return {"text": "Crawled locally.", "code": 200}
        else:
            future = executor.submit(route_handler.upsert_review_batch, payload)
            # res_text, res_code = route_handler.upsert_review_batch(payload)
            # log.info(f"[INFO] {res_text}, {res_code}")
            future.add_done_callback(clear_callback)
            # return {"text": res_text, "code": res_code}        
        

def review_crawler(
        category:str, 
        type:str,
        headless=False, 
        active_user_agent=False, 
        use_proxy=False,
        for_local_test=True,
        for_local_api_test=True,
        max_ocr_workers=4
    ) -> bool:
        
    naver_shopping_driver = Driver(headless=headless, active_user_agent=active_user_agent, use_proxy=use_proxy, get_log=True)        
    
    s_category_row = route_handler.get_category(s_category=category)
    caid = s_category_row[0]['caid']               

    products = route_handler.get_product(caid=caid)
    
    # 이미 크롤링한 데이터가 있으면 삭제하는 로직.
    # global start_date, json_save_fp    
    # if for_local_test and (
    #     os.path.exists(f"./{json_save_fp}/{start_date}_{category}_review") 
    #     or os.path.exists(f"./{json_save_fp}/{start_date}_{category}_ocr")
    #     ):
    #     log.warning(f"[WARNING] {category}_review directory already exists. DELETE IT.")                   
    #     if os.path.exists(f"./{json_save_fp}/{start_date}_{category}_review"):
    #         rmtree(f"./{json_save_fp}/{start_date}_{category}_review")            
    #     if os.path.exists(f"./{json_save_fp}/{start_date}_{category}_ocr"):
    #         rmtree(f"./{json_save_fp}/{start_date}_{category}_review")               
    flag = False
    try:
        for product in products: 
            
            # if "힉스코리아" not in product['name']:
            #     continue
            # if "맥세이프" in product['name']:
            #     continue

            prod_dict = {
                    "grade": "",
                    "name": "",
                    "lowest_price": "",
                    "review_count": "",
                    "url": "",
                    "brand": "",
                    "maker": "",
                    "naver_spec": "",
                    "seller_spec": "",
                    "detail_image_urls": "",
                }
            for key in product.keys():
                prod_dict[key] = product[key]                    
                

            url = product['url']
            name = product['name']
            
            naver_shopping_driver.get(url)
            naver_shopping_driver.set_current_url()
            log.info(f"[INFO] Start crawling at {name}.")

            # TODO: test cases:
            # 디알고 헤드셋. 적은 평점.
            # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
            # 어프어프. 리뷰 없음.
            # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/45960130619?&NaPm=ct%3Dludqbeyg%7Cci%3Dc6cf7cf700e756c885e4e7e9829c11d935a7e990%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dbc572d7cb475be323262c78ba2bdd1074c1f6d81")
            # 로지텍 K830: 리뷰 27000개
            # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/8974763652?&NaPm=ct%3Dlucr5xuw%7Cci%3D5549087459ddae34d93daf8f0d9e0686cf56ea87%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3D784343aaa845130bbe75468952f58e847fc0499c")
                    
            while use_proxy and is_banned(naver_shopping_driver) :
                pass

            # get product detail    
            try:
                brand, maker, grade, name, lowest_price = fetch_product_detail(naver_shopping_driver)
            except:
                log.warning("[WARNING] No floating tabs. Skip this product.") # 연량확인 필요한 제품인 경우도 존재.
                continue     
                    
            log.info(f"[INFO] Brand: {brand}, Maker: {maker}")
            prod_dict["brand"] = brand
            prod_dict["maker"] = maker
            if grade != -1:
                prod_dict["grade"] = grade
            if name != "":
                prod_dict["name"] = name
            if lowest_price != -1:
                prod_dict["lowest_price"] = lowest_price        
                    
            # 제품 상세 보러가기        
            floating_tabs = naver_shopping_driver.wait_until_by_xpath(10, ".//div[contains(@class, 'floatingTab_detail_tab')]")                
            
            tabs = floating_tabs.find_elements(By.XPATH, ".//li")
            product_details = None
            review_tab = None
            # for initialization.
            if len(tabs) > 2:
                product_details = tabs[1]
                review_tab = tabs[2]
            for tab in tabs:
                if '제품정보' in tab.text:
                    product_details = tab
                elif '쇼핑몰리뷰' in tab.text:
                    review_tab = tab

            # 리뷰 개수 가져오기.
            if review_tab:        
                review_count_text = review_tab.find_element(By.XPATH, ".//em").text
                review_count = int(review_count_text.replace(",", "").replace("개", ""))
                prod_dict["review_count"] = review_count

            if product_details:
                naver_shopping_driver.move_to_element(element=product_details)
                product_details.click()

            # 제품 상세 더보기 있는 경우와 없는 경우 둘 다 있음.
            try:
                btn_detail_more = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'imageSpecInfo_btn_detail_more')]")
                naver_shopping_driver.move_to_element(element=btn_detail_more)
                btn_detail_more.click()
            except:
                log.warning("[WARNING] No see more button.")
            
            
            
            
            
            ## [SPEC]
            
            # 제품 상세에서 ocr 및 location 따기                
            naver_spec, seller_spec, img_urls = get_product_spec(naver_shopping_driver, max_ocr_workers=max_ocr_workers )

            # naver_spec 없으면 더보기로 클릭해서 가져옴.
            if not naver_spec and seller_spec:
                naver_spec = fetch_spec(naver_shopping_driver)            
            
            # seller_spec (image_spec 없으면 바로 다음 제품)
            if not seller_spec:
                log.info(f"[WARNING] No seller spec in {name}. Go to next product.")
                continue
            
            if for_local_test and seller_spec:
                if not os.path.exists(f"./{json_save_fp}/{start_date}_{category}_ocr"):
                    os.makedirs(f"./{json_save_fp}/{start_date}_{category}_ocr")
                current_time = datetime.datetime.now().strftime("%Y%m%d_%Hh%Mm%Ss")        
                with open(f"./{json_save_fp}/{start_date}_{category}_ocr/{current_time}_{prod_dict['prid']}.json", 'w', encoding='utf-8-sig') as json_file:                                                         
                    json.dump(seller_spec, json_file, ensure_ascii=False, indent=4)            
                
                    
            log.info(f"[INFO] Spec: {naver_spec}")
            prod_dict["naver_spec"] = naver_spec  
            prod_dict["seller_spec"] = seller_spec
            prod_dict["detail_image_urls"] = img_urls

            ## fetch product detail
            if not for_local_test:
                future = executor.submit(route_handler.update_product_detail_one, data=prod_dict)
                future.add_done_callback(lambda future: log.info(f"[INFO] {future.result()}"))
                # res_text, res_code = route_handler.update_product_detail_one(data=prod_dict)      
                # log.info(f"[INFO] {name} product detail updated. Response: {res_text}, Code: {res_code}")

            # 리뷰 크롤링하기.
            review_filters = naver_shopping_driver.driver.find_elements(By.XPATH, ".//ul[contains(@class, 'filter_top_list_')]/li")
            review_filters.pop(0) # 필터 중 전체 별점 제거.
            # 필요 없는 log 제거.
            naver_shopping_driver.flush_log()
            
            # 리뷰가 없는 제품인 경우. 스킵함.
            try:
                # sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # 과거임.
                sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-shp-area, 'rev.sort')]") # recent라는 뜻임.
            except Exception as e:
                log.warning(f"[WARNING] No Reviews in {name}. Go to next product.")
                continue
                
            # Marking
            current_review_filter_score = review_filters[0].text.split(" ")[0] # 초기값은 첫번째 필터의 "n점"
            current_page_num = 1
            retry_count = 0
            
            
            review_crawling_done = False
            while not review_crawling_done:
                if retry_count > 3:
                    log.warning(f"[WARNING] Review crawling count over 3. Go to next product.")
                    break
                retry_count += 1

                flag_until_banned_review_filter = False
                flag_until_banned_page_num = False
                for review_filter in review_filters:
                    # IP Blocked 시 다시 driver를 띄울 때, 리뷰 grade를 특정 수치로 설정해서 넘어가게끔 함.                                
                    if is_banned(naver_shopping_driver):
                        break
                    # 조기 종료.
                    if review_crawling_done:
                        break
                    if flag_until_banned_review_filter or current_review_filter_score == review_filter.text.split(" ")[0]:
                        flag_until_banned_review_filter = True                    
                    if not flag_until_banned_review_filter:
                        continue                

                    # click하고 밴 체크 -> 동일한 패턴임.
                    naver_shopping_driver.move_to_element(review_filter)
                    review_filter.click()
                    time.sleep(random.randint(4,8)*0.5)
                    if is_banned(naver_shopping_driver):
                        break

                    current_review_filter_score = review_filter.text.split(" ")[0]
                    is_last_page = False
                    
                    # 100개 이상이면 리뷰가 없음.
                    while (not is_last_page 
                        and current_page_num < 102 # prevent while infinite loop.
                        ): 
                        review_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'review_section_review')]")
                        review_pages = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'pagination_pagination')]/a")                            

                        if not review_pages: # 리뷰 자체가 한 페이지면 리뷰 로그 얻고 종료.
                            is_last_page = True                           
                                                                
                            upsert_review(
                                naver_shopping_driver, 
                                prid=prod_dict['prid'], 
                                match_nv_mid=prod_dict.get('match_nv_mid'), 
                                s_category=category, type=type,
                                for_local_test=for_local_test
                                )        
                                        
                            continue

                        if 'next' not in review_pages[-1].get_attribute('class'): # next라는게 없을 때까지 -> 리뷰의 끝까지.
                            is_last_page = True
                        
                        if (for_local_api_test or for_local_test) and current_page_num > 2:
                            review_crawling_done = True
                            break    
                        

                        for review_page in review_pages:
                            # move_to_marker = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'reviewItems_btn_area')]")[-1]
                            time.sleep(random.randint(4,8)*0.5)
                            if is_banned(naver_shopping_driver):
                                is_last_page = True
                                break
                            
                            is_current_page = 'now' in review_page.get_attribute('class')
                            is_prev_pages_button = 'prev' in review_page.get_attribute('class')
                            
                            if is_prev_pages_button:
                                continue
                            elif is_current_page:
                                current_page_num+=1
                                if (for_local_api_test or for_local_test) and current_page_num > 2:
                                    review_crawling_done = True
                                    break                                
                                                                                
                                upsert_review(
                                    naver_shopping_driver, 
                                    prid=prod_dict['prid'], 
                                    match_nv_mid=prod_dict.get('match_nv_mid'), 
                                    s_category=category, type=type,
                                    for_local_test=for_local_test
                                    )       
                                continue
                            
                            if not flag_until_banned_page_num and '다음' in review_page.text:
                                review_page.click()
                                continue

                            if flag_until_banned_page_num or current_page_num == int(review_page.text):
                                flag_until_banned_page_num = True                    
                            
                            if not flag_until_banned_page_num:
                                continue        

                            log.info(f"[INFO] Current page_num: {current_page_num}")

                            naver_shopping_driver.move_to_element(element=review_page)
                            review_page.click()

                            try:
                                # 100 페이지를 넘어가려고 하면 경고가 나옴.
                                naver_shopping_driver.driver.switch_to.alert.accept()
                                log.warning(f"[WARNING] Over 2000+ review.")
                                is_last_page = True
                                break
                            except:
                                pass
                            time.sleep(random.randint(4,8)*0.5)        
                            if (for_local_api_test or for_local_test) and current_page_num > 2:
                                review_crawling_done = True
                                break    
                                                                                        
                            upsert_review(
                                naver_shopping_driver, 
                                prid=prod_dict['prid'], 
                                match_nv_mid=prod_dict.get('match_nv_mid'), 
                                s_category=category, type=type,
                                for_local_test=for_local_test
                                )       
                            current_page_num+=1
                    
                review_crawling_done = True
            
            log.info(f"[SUCCESS] {name} crawled complete.")    
        return True
    except Exception:        
        log.error(f"[ERROR] {traceback.format_exc()}")
        return False
                
    finally:
        naver_shopping_driver.release()
        


if __name__ == '__main__':    
    # for category in ["tv"]:
    for category in ["humidifier"]:
        parser = ArgumentParser(description='Review crawler for naver shopping. Enter the category.')
        parser.add_argument('--category', type=str, help='Enter the category you want to crawl.', default=category)
        parser.add_argument('--headless', type=bool, help='Set headless mode.', default=False)
        parser.add_argument('--use_proxy', type=bool, help='Set use proxy ip.', default=False)
        parser.add_argument('--active_user_agent', type=bool, help='Active user agent.', default=False)
        parser.add_argument('--type', type=str, help='Enter the type.', default="R0")    
        parser.add_argument('--for_local_test', type=bool, help='Is for crawl data locally, or crawl data for service', 
                            default=False)    
        parser.add_argument('--for_local_api_test', type=bool, help='Is for crawl data and local api test', 
                            default=True)    
        
        args = parser.parse_args()

        log.info(f"[INFO] Start crawling at {args.category}")
        log.info(f"[INFO] Headless: {args.headless}, Use proxy: {args.use_proxy}, Active user agent: {args.active_user_agent}")
        
        global start_date, json_save_fp
        if args.for_local_test:
            json_save_fp = f"./crawled_data"
            if not os.path.exists(f"./{json_save_fp}"):
                os.makedirs(f"./{json_save_fp}")
    
        start_date = datetime.datetime.now().strftime("%Y%m%d")
        
        result = review_crawler(
            category=args.category, 
            headless=args.headless, 
            active_user_agent=args.active_user_agent, 
            use_proxy=args.use_proxy,
            type=args.type,
            for_local_test=args.for_local_test,
            for_local_api_test=args.for_local_api_test,
            )    
        if result:
            log.info(f"[SUCCESS] Success at {args.category}")
        else:
            log.error(f"[ERROR] Error at {args.category}")