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


def fetch_product_details(driver:Driver, name:str):
    # TODO: # 사진 캡처하기. (단, OCR 인식 후에 제품정보 ~ 본 컨텐츠는... 까지 y 좌표 어긋나면 다 주기.)
    spec_info_section = driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")
    driver.move_to_element(element=spec_info_section)

    page_location_dict = {}
    # 스펙 부분 위치.
    product_detail = driver.driver.find_element(By.ID, "section_spec")
    page_location_dict['product_detail'] = product_detail.location
    # 본 컨텐츠는 ... 부분 위치.
    try:
        imageSpecInfo_provide = driver.wait_until_by_xpath(3, ".//p[contains(@class, 'imageSpecInfo_provide_')]")
        page_location_dict['spec_info_provide'] = imageSpecInfo_provide.location
    except:
        SpecInfo_provide = driver.wait_until_by_xpath(3, ".//p[contains(@class, 'specInfo_provide_')]")
        page_location_dict['spec_info_provide'] = SpecInfo_provide.location
        

    # 전체 페이지 높이 가져오기
    total_height = driver.driver.execute_script("return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);")
    # 전체 페이지 너비 가져오기
    total_width = driver.driver.execute_script("return Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);")
    page_location_dict['total'] = {'x': total_width, 'y': total_height}

    with open(f'./product_detail_location/{name}_product_detail.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(page_location_dict, json_file, ensure_ascii=False)


    # 제품정보 섹션 캡처.
    S = lambda X: driver.driver.execute_script('return document.getElementById("section_spec").'+X)
    driver.driver.set_window_size(S('clientWidth'), S('clientHeight')+100)
    driver.driver.save_screenshot(f'./product_detail_images/{name}_product_detail.png')
    log.info(f"[INFO] Captured screenshot at {name}")
    
    # 다시 이전 크기로 복귀.
    driver.driver.set_window_size(1920, 1080)

    # b64_image = driver.driver.find_element(By.TAG_NAME, 'body').screenshot_as_base64
    # img_file = BytesIO(b64_image)
    # img = Image.open(img_file)
    # img_asarray = numpy.asarray(img)



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
    product_links, product_names, category = get_links("./api_call/20240330_15h10m_extra_battery_product_link.json")

    for link, name in zip(product_links, product_names):
        naver_shopping_driver = Driver(headless=True, active_user_agent=True, get_log=False)
        # 원래는 크롤링한 사이트 링크들.
        naver_shopping_driver.get(link)
        
        # TODO: Test cases:
        # 디알고 헤드셋. 적은 평점.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
        # 어프어프. 리뷰 없음.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/45960130619?&NaPm=ct%3Dludqbeyg%7Cci%3Dc6cf7cf700e756c885e4e7e9829c11d935a7e990%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dbc572d7cb475be323262c78ba2bdd1074c1f6d81")
        # 로지텍 K830: 리뷰 27000개
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/8974763652?&NaPm=ct%3Dlucr5xuw%7Cci%3D5549087459ddae34d93daf8f0d9e0686cf56ea87%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3D784343aaa845130bbe75468952f58e847fc0499c")
        # 문제 생겼던 링크 (window size 때문)
        # naver_shopping_driver.get("https://cr.shopping.naver.com/adcr.nhn?x=3wvfZtZGmceSs641Ml%2FJKf%2F%2F%2Fw%3D%3Ds8xsBat77RWM1DzBc66pPxs9iMNnNYse%2FP%2FQko4MiSoG4mM1CYTkB27IqxY103un83MogR91s%2BkMfNiNtvigU3%2F3F13OdIFbQ4eIqobl30eSnjU4RahHEtGRBKfzgyFGKRsCh5GS%2BklokEzA%2FJ0VszxCGSQdcrj%2BZJHLmJxgT%2Fbv5fZFoZgwbE%2FZ%2Bo%2FI6GKKfMNpwjPd8mI%2FlZ293IqVcUyAVdAOGxptQe6SJREotCfgHs%2F2PHkpmvWjL2qy1nHubEKK%2FkpYkwP7L1JPwnXYdgQnl1JZtBOJBsv4ALUhUiXuavKtHPoJr7KcoQSnIR2I4b6ZpwGVgEbAFQngQWnXt8bY72nrZTSSgDrZ5Ba2B3jhIo7WUwD%2FWxwtE7nksusXyC0r%2BUmM4rOUlXYgQF%2BmvEdBbefWDCD8uwakSuS0VR1KDYZBJ2nBNNVuwxntyfU6jWUxZxFxYCXkSqLO%2FKtFdSdf19%2BjNbO2H24LvW62V2wcJ39uGOv9OPijfMg0hrHJMD7KxOqdqDKdRpcdo%2FZT1gHQuQPHdfxBpbbO8x0VVjYa2wjCtrIYHbwONe4aQ3le%2Bse2SMPk0CcDbXY79FaFPAV2%2B%2FxyXlCSAWzA7%2BLQj8t8%3D&nvMid=45584092618&catId=50004603")
        
        floating_tabs = naver_shopping_driver.wait_until_by_xpath(5, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        product_details = floating_tabs.find_elements(By.XPATH, ".//li")[1]
        # 브랜드 insert.
        brand, maker = fetch_brand_maker(naver_shopping_driver)
        log.info(f"[INFO] Brand: {brand}, Maker: {maker}")
        
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
            time.sleep(15)
        except:
            log.warning("[WARNING] No see more button.")
            time.sleep(15)
        
        fetch_product_details(naver_shopping_driver, name)
        naver_shopping_driver.release()


if __name__ == '__main__':
    test()



