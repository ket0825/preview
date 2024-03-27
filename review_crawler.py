#stdlib
import json
import time
import random
import datetime
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from PIL import Image
import base64
from io import BytesIO

# custom lib.
from log import Logger 
log = Logger.get_instance()

def get_links(path:str) -> list:
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        product_raw_json = json.load(json_file)
        links = [ item['url'] for item in product_raw_json['items']]
        return links

def test():
    naver_shopping_driver = Driver(headless=True)
    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    # XPATH 예시들.
    """https://selenium-python.readthedocs.io/locating-elements.html"""
    product_links = get_links("./api_call/20240328_02h56m_extra_battery_product_link.json")

    for link in product_links:
        # 원래는 크롤링한 사이트 링크들.
        
        naver_shopping_driver.get(link)
        # 디알고 헤드셋.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
        
        # naver_shopping_driver.wait_until_by_css_selector(3)
        sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # recent라는 뜻임.
        floating_tabs = naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        product_details = floating_tabs.find_elements(By.XPATH, ".//li")[1]
        naver_shopping_driver.move_to_element(element=product_details)
        product_details.click()

        # 있는 경우와 없는 경우 둘 다 있음.
        try:
            btn_detail_more = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'imageSpecInfo_btn_detail_more')]")
            naver_shopping_driver.move_to_element(element=btn_detail_more)
            btn_detail_more.click()
        except:
            log.warning("[WARNING] No detail more button.")
        
        # 사진 캡처하기. (단, OCR 인식 후에 제품정보 ~ 본 컨텐츠는... 까지 y 좌표 어긋나면 다 주기.)
        spec_info_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")
        naver_shopping_driver.move_to_element(element=spec_info_section)

        # 제품정보 섹션 캡처
        # S = lambda X: naver_shopping_driver.driver.execute_script('return document.getElementById("section_spec").'+X)
        # naver_shopping_driver.driver.set_window_size(S('clientWidth'), S('clientHeight'))
        # naver_shopping_driver.driver.find_element(By.TAG_NAME, 'body').screenshot('spec_full_img3.png')

        # 제품정보 섹션이 아닌, 전체 캡처
        S = lambda X: naver_shopping_driver.driver.execute_script('return document.body.parentNode.scroll'+X)
        naver_shopping_driver.driver.set_window_size(S('Width'), S('Height'))
        naver_shopping_driver.driver.find_element(By.TAG_NAME, 'body').screenshot('spec_full_img.png')
        
        naver_shopping_driver.move_to_element(element=sort_by_recent)
        try:
            sort_by_recent.click() 
        except:
            # Can't click when the element did not appear to display.
            log.info(f"[ERROR]: Click misses: {sort_by_recent}")
            return
        
        is_last_page = False
        page_num = 1
        
        while not is_last_page:
            review_section = naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'review_section_review')]")
            review_pages = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'pagination_pagination')]/a")        

            if 'next' not in review_pages[-1].get_attribute('class'): # next라는게 없을 때까지 -> 리뷰의 끝까지.
                is_last_page = True

            for review_page in review_pages:
                # move_to_marker = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'reviewItems_btn_area')]")[-1]
                if page_num == 90:
                    log.info(review_pages)
                is_current_page = 'now' in review_page.get_attribute('class')
                is_prev_pages_button = 'prev' in review_page.get_attribute('class')
                
                if is_prev_pages_button or is_current_page:
                    continue
                
                log.info(f"[INFO] Current page_num: {page_num}")
        
                naver_shopping_driver.move_to_element(element=review_page)
                review_page.click()
                time.sleep(random.randint(2,6)*0.5)
                
                page_num+=1
            
        time.sleep(1) # 기다려야 log가 수집됨.
        
        chrome_logs_raw = naver_shopping_driver.driver.get_log("performance")
        chrome_logs = [json.loads(lr["message"])["message"] for lr in chrome_logs_raw]

        def log_filter(log_):
            return (
                # is an actual response
                log_["method"] == "Network.responseReceived"
                # and json
                and "json" in log_["params"]["response"]["mimeType"]
            )
        
        total_reviews = []

        for log_ in filter(log_filter, chrome_logs):
            request_id = log_["params"]["requestId"]
            resp_url = log_["params"]["response"]["url"]
            if 'review' in resp_url:    # review url:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
                log.info(f"Caught {resp_url}")        
                reviews = json.loads(naver_shopping_driver.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body'])['reviews']
                total_reviews.extend(reviews) # extend
                # 원래는 reviews 할 때 마다 api call로 db에 넣을 예정임. 지금은 임시로 json으로 나옴.
        
        # for review in total_reviews:
        #     log.info(review)            
                
        current_time = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm')

        with open(f'./{current_time}_review.json', 'w', encoding='utf-8-sig') as json_file:
            log.info("Review data from JSON file completed.")
            json.dump(total_reviews, json_file, ensure_ascii=False)

        naver_shopping_driver.release()


if __name__ == '__main__':
    test()



