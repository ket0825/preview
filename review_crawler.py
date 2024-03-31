# 태그 매치
"""https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
# XPATH 예시들.
"""https://selenium-python.readthedocs.io/locating-elements.html"""

# TODO:
"""
남은 것: 
1. IP 밴 먹기 처리.
2. OCR 처리.
"""

#stdlib
import json
import time
import random
import datetime
from io import BytesIO
import re
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from bs4 import BeautifulSoup
from PIL import Image
import numpy



# custom lib.
from log import Logger 
log = Logger.get_instance()

global total_reviews
total_reviews = []
double_space_ptrn = re.compile(r" {2,}")
double_newline_ptrn = re.compile(r"\n{2,}")
access_word_ptrn = re.compile(r"[^가-힣ㄱ-ㅎㅏ-ㅣ0-9a-zA-Z\s'\"@_#$\^&*\(\)\-=+<>\/\|}{~:…℃±·°※￦\[\]÷\\;,\s]")

def get_links(path:str) -> list:
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        product_raw_json = json.load(json_file)
        links = [item['url'] for item in product_raw_json['items']]
        product_names = [item['name'] for item in product_raw_json['items']]
        category = product_raw_json['category']
        return links, product_names, category, 


def fetch_brand_maker(driver: Driver):
    top_info = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'top_info_inner_')]")[0]
    top_cells = top_info.find_elements(By.XPATH, ".//span[contains(@class, 'top_cell_')]")
    brand = ""
    maker = ""
    for cell in top_cells:
        if '브랜드' not in cell.text and '제조사' not in cell.text:
            continue
        if '브랜드' in cell.text and '카탈로그' not in cell.text:
            brand = cell.text.replace("브랜드","").replace(" ","")
        elif '제조사' in cell.text:
            maker = cell.text.replace("제조사","").replace(" ","")

    # TODO: fetch 진행.
    return brand, maker


def fetch_spec(driver:Driver):    
    driver.driver.find_element(By.XPATH, ".//a[contains(@class, 'top_more_')]").click() # 더 보기 클릭.
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

    # TODO: fetch 진행
    return spec_dict


def fetch_product_details(driver:Driver):
    # TODO: # 사진 캡처하기. (단, OCR 인식 후에 제품정보 ~ 본 컨텐츠는... 까지 y 좌표 어긋나면 다 주기.)
    # spec_info_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")
    # naver_shopping_driver.move_to_element(element=spec_info_section)
        
    # 제품정보 섹션 캡처
    S = lambda X: driver.driver.execute_script('return document.getElementById("section_spec").'+X)
    driver.driver.set_window_size(S('clientWidth'), S('clientHeight'))
    b64_image = driver.driver.find_element(By.TAG_NAME, 'body').screenshot_as_base64
    img_file = BytesIO(b64_image)
    img = Image.open(img_file)
    img_asarray = numpy.asarray(img)





def get_review_log(driver: Driver):
    """
    Flush log buffer and append total_reviews.
    """
    chrome_logs_raw = driver.driver.get_log("performance")
    chrome_logs = [json.loads(lr["message"])["message"] for lr in chrome_logs_raw]

    for log_ in filter(log_filter, chrome_logs):
        request_id = log_["params"]["requestId"]
        resp_url = log_["params"]["response"]["url"]
        if 'review' in resp_url:    
            # review url 구조:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
            log.info(f"Caught {resp_url}")        
            reviews = json.loads(driver.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body'])['reviews']
            review_formatter(reviews)
            total_reviews.extend(reviews) # extend
            # 원래는 reviews 할 때 마다 api call로 db에 넣을 예정임. 지금은 임시로 json으로 나옴.

    # for review in total_reviews:
    #     log.info(review)

def review_formatter(reviews:list[dict]) -> None:
    # remain_key = ['id', 'content', 'aidaModifyTime', 'mallId', 'mallSeq', 'matchNvMid', 'qualityScore', 'starScore', 'topicCount', "topicYn", 'topics', 'userId', 'mallName']    
    keys_to_remove = ["buyOption", "aidaCreateTime", "esModifyTime", "modifyDate", "pageUrl", "registerDate", "imageCount", "imageYn", "images", "mallProductId", "mallReviewId", "rankScore", "title", "videoCount", "videoYn", "videos", "mallLogoUrl"]
    for review in reviews:
        for key in keys_to_remove:
            review.pop(key)
        
        review['content'] = review['content'].replace('<br>', '\n')\
                                            .replace('<br/>', '\n')\
                                            .replace("\r\n", "\n")\
                                            .replace("\r", "\n")
        
        review['content'] = BeautifulSoup(review['content'], 'lxml').text
        review['content'] = access_word_ptrn.sub("", review['content'])
        review['content'] = double_space_ptrn.sub(" ", review['content'])
        review['content'] = double_newline_ptrn.sub("\n", review['content'])


def log_filter(log_):
    return (
        # is an actual response
        log_["method"] == "Network.responseReceived"
        # and json
        and "json" in log_["params"]["response"]["mimeType"]
    )


def flush_log(driver:Driver):
    driver.driver.get_log('performance')


def test():
    naver_shopping_driver = Driver(headless=False)
    product_links, product_names, category = get_links("./api_call/20240330_15h10m_extra_battery_product_link.json")

    for link, name in zip(product_links, product_names):
        # 원래는 크롤링한 사이트 링크들.
        
        naver_shopping_driver.get(link)
        # TODO: T cases:
        # 디알고 헤드셋. 적은 평점.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
        # 어프어프. 리뷰 없음.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/45960130619?&NaPm=ct%3Dludqbeyg%7Cci%3Dc6cf7cf700e756c885e4e7e9829c11d935a7e990%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dbc572d7cb475be323262c78ba2bdd1074c1f6d81")
        # 로지텍 K830: 리뷰 27000개
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/8974763652?&NaPm=ct%3Dlucr5xuw%7Cci%3D5549087459ddae34d93daf8f0d9e0686cf56ea87%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3D784343aaa845130bbe75468952f58e847fc0499c")

        # 브랜드 insert.
        brand, maker = fetch_brand_maker(naver_shopping_driver)
        log.info(f"[INFO] Brand: {brand}, Maker: {maker}")

        # naver_shopping_driver.wait_until_by_css_selector(3)
        floating_tabs = naver_shopping_driver.wait_until_by_xpath(5, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        product_details = floating_tabs.find_elements(By.XPATH, ".//li")[1]
        
        # 리뷰가 없는 제품인 경우.
        try:
            sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # recent라는 뜻임.
        except Exception as e:
            log.warning(f"[WARNING] No Reviews in {name}. Go to next product.")
            continue

        naver_shopping_driver.move_to_element(element=product_details)
        product_details.click()

        # 제품 상세 더보기 있는 경우와 없는 경우 둘 다 있음.
        try:
            btn_detail_more = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'imageSpecInfo_btn_detail_more')]")
            naver_shopping_driver.move_to_element(element=btn_detail_more)
            btn_detail_more.click()
        except:
            log.warning("[WARNING] No see more button.")
        
        fetch_product_details(naver_shopping_driver)
            
        spec = fetch_spec(naver_shopping_driver)            
        log.info(f"[INFO] Spec: {spec}")

        review_filters = naver_shopping_driver.driver.find_elements(By.XPATH, ".//ul[contains(@class, 'filter_top_list_')]/li")
        review_filters.pop(0) # 필터 중 전체 별점 제거.
        
        flush_log(naver_shopping_driver) # 필요 없는 log 제거.

        for review_filter in review_filters:
            naver_shopping_driver.move_to_element(element=sort_by_recent)
            review_filter.click()
            time.sleep(random.randint(4,8)*0.5)
            is_last_page = False
            page_num = 1
            # 100개 이상이면 리뷰가 없음.
            while (not is_last_page 
                and page_num < 102 # prevent while infinite loop.
                ): 
                review_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'review_section_review')]")
                review_pages = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'pagination_pagination')]/a")        
                
                if not review_pages: # 리뷰 자체가 한 페이지면 리뷰 로그 얻고 종료.
                    is_last_page = True
                    get_review_log(naver_shopping_driver)
                    continue

                if 'next' not in review_pages[-1].get_attribute('class'): # next라는게 없을 때까지 -> 리뷰의 끝까지.
                    is_last_page = True

                for review_page in review_pages:
                    # move_to_marker = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'reviewItems_btn_area')]")[-1]
                    is_current_page = 'now' in review_page.get_attribute('class')
                    is_prev_pages_button = 'prev' in review_page.get_attribute('class')
                    
                    if is_prev_pages_button or is_current_page:
                        continue
                    
                    log.info(f"[INFO] Current page_num: {page_num}")

                    if page_num == 100:
                        print("")

                    naver_shopping_driver.move_to_element(element=review_page)
                    review_page.click()

                    try:
                        naver_shopping_driver.driver.switch_to.alert.accept()
                        log.warning(f"[WARNING] Over 2000+ review.")
                        is_last_page = True
                        break
                    except:
                        pass

                    time.sleep(random.randint(4,8)*0.5)
                    get_review_log(naver_shopping_driver)                
                    page_num+=1
    
            current_time = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss')            
            
            # 후에는 product_id로 할 것임.
            with open(f'./reviews/{current_time}_{category}_{name}_review.json', 'w', encoding='utf-8-sig') as json_file:
                log.info("Review data from JSON file completed.")
                json.dump(total_reviews, json_file, ensure_ascii=False)
            
            total_reviews.clear()


    naver_shopping_driver.release()


if __name__ == '__main__':
    test()



