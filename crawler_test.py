# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By

# custom lib.
from log import Logger 
log = Logger.get_instance()

def test():
    category = 'smartwatch'
    naver_shopping_driver = Driver(headless=False)

    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    # XPATH 예시들.
    """https://selenium-python.readthedocs.io/locating-elements.html"""
    # XPATH substring match.
    # link = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')/a]") 
    # CSS_SELECTOR substring match.
    # link = naver_shopping_driver.driver.find_elements(By.CSS_SELECTOR, "div[class*='reviewItems_title']") # substring match.
    
    naver_shopping_driver.get_url_by_category(category)
    naver_shopping_driver.wait(5)
    # # username = driver.find_element(By.XPATH, "//form[input/@name='username']")
    a_tags = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')]/a[@href]") # substring match.
    
    for a_tag in a_tags:
        log.info(f"link: {a_tag.get_attribute('href')}")

    naver_shopping_driver.go_next_page()
    a_tags = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')]/a[@href]") # substring match.
    for a_tag in a_tags:
        log.info(f"link: {a_tag.get_attribute('href')}")

    # 리뷰 쿼리:"https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=42620727618&page=4&pageSize=20&sortType=RECENT"
    # TODO: network 확인.
    # headers = {
    # "Accept": "application/json, text/plain, */*",
    # "Accept-Encoding": "gzip, deflate, br",
    # "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    # "Cookie": "",  # 실제 쿠키 값 입력
    # "Dnt": "1",
    # "Referer": "https://search.shopping.naver.com/catalog/41438134618?&NaPm=ct%3Dlu03bvig%7Cci%3Dd5bc94763ffed9c534d4d2b0f3651f852e00ac05%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dcf893e9e08f5a7ed5c57998bf3eaeab7a5c2a324",
    # "Sbth": "c4d56949d3f08269430ef301c81e1797c17a5c3b4a3156aa5f4ef53a7a06db25d2746a713596986a2824d2736e145db4",
    # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    # }

    # # Chrome DevTools Protocol 명령 실행
    # cmd = "Network.setExtraHTTPHeaders"
    # params = {"headers": headers}
    # naver_shopping_driver.driver.execute_cdp_cmd(cmd, params)

    # url = "https://search.shopping.naver.com/api/review?isNeedAggregation=N&nvMid=41438134618&page=1&pageSize=20&sortType=RECENT"
    # response = naver_shopping_driver.driver.execute_cdp_cmd("Network.sendRequestWithContext", {"url": url, "method": "GET"})

    # # 응답 처리
    # if response.get("success"):
    #     body = response.get("response", {}).get("body", "")
    #     print(body)
    # else:
    #     error = response.get("message")
    #     print(f"Error: {error}")

    naver_shopping_driver.release()


if __name__ == '__main__':
    test()
    