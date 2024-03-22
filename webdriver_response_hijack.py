#stdlib
import json
import time
import random
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By


# custom lib.
from log import Logger 
log = Logger.get_instance()

xhr_pattern = r"XMLHttpRequest"

def test():
    category = 'smartwatch'
    naver_shopping_driver = Driver(headless=False)

    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    # XPATH 예시들.
    """https://selenium-python.readthedocs.io/locating-elements.html"""

    # 아이폰
    naver_shopping_driver.get("https://search.shopping.naver.com/catalog/42617437619?&NaPm=ct%3Dlu1a619c%7Cci%3D9a989f171d581b33e94796aa84f47af8e526ac37%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Db1354d632187303e9f2c56687a8afd0ad88ef9b0")
    # 디알고 헤드셋.
    # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")

    # naver_shopping_driver.wait_until_by_css_selector(3)
    sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, "//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # recent라는 뜻임.
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
        review_section = naver_shopping_driver.driver.find_element(By.XPATH, "//div[contains(@class, 'review_section_review')]")
        review_pagination = review_section.find_element(By.XPATH, ".//div[contains(@class, 'pagination_pagination')]")
        review_pages = review_pagination.find_elements(By.XPATH, ".//a")
        x, y = review_section.find_elements(By.XPATH, ".//div[contains(@class, 'reviewItems_review')]")[-1].location
        
        for page in review_pages:
            
            if page_num == 90:
                log.info(review_pages)
            is_current_page = 'now' in page.get_attribute('class')
            is_prev_pages_button = 'prev' in page.get_attribute('class')
            
            if is_prev_pages_button or is_current_page:
                continue
            
            log.info(f"[INFO] Current page_num: {page_num}")
            naver_shopping_driver.driver.execute_script("scrollTo(arguments[0],arguments[1])", x, y)
    
            # naver_shopping_driver.move_to_element(element=move_to_marker)
            time.sleep(random.randint(2,6)*0.5)
            page.click()
            page_num+=1

        

        if 'next' not in review_pages[-1].get_attribute('class'):
            is_last_page = True

        
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
            # 원래는 reviews 할 때 마다 api call로 db에 넣을 예정임. 지금은 임시.
    
    # for review in total_reviews:
    #     log.info(review)            
    
    with open('review.json', 'w', encoding='utf-8-sig') as json_file:
        log.info("Review data from JSON file completed.")
        json.dump(total_reviews, json_file, ensure_ascii=False)

    naver_shopping_driver.release()


if __name__ == '__main__':
    test()



