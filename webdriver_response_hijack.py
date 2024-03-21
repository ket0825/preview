#stdlib
import json
import time
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

    naver_shopping_driver.get("https://search.shopping.naver.com/catalog/42617437619?&NaPm=ct%3Dlu1a619c%7Cci%3D9a989f171d581b33e94796aa84f47af8e526ac37%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Db1354d632187303e9f2c56687a8afd0ad88ef9b0")
    naver_shopping_driver.wait(3)
    
    sort_by_recent = naver_shopping_driver.driver.find_elements(By.XPATH, "//a[contains(@class, 'filter_sort')]")[1]    
    sort_by_recent.click() # OK.
    time.sleep(2)

    logs_raw = naver_shopping_driver.driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
    def log_filter(log_):
        return (
            # is an actual response
            log_["method"] == "Network.responseReceived"
            # and json
            and "json" in log_["params"]["response"]["mimeType"]
        )
    reviews = []
    for log_ in filter(log_filter, logs):
        request_id = log_["params"]["requestId"]
        resp_url = log_["params"]["response"]["url"]
        if 'review' in resp_url:    # review url:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
            log.info(f"Caught {resp_url}")        
            reviews = json.loads(naver_shopping_driver.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})['body'])['reviews']
            break

    for review in reviews:
        print(review)
    
    naver_shopping_driver.release()


if __name__ == '__main__':
    test()



