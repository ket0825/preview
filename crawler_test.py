
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
## Option 목록.
# #지정한 user-agent로 설정합니다.
# user_agent = "Mozilla/5.0 (Linux; Android 9; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Mobile Safari/537.36"
# options.add_argument('user-agent=' + user_agent)

# options.add_argument('headless') #headless모드 브라우저가 뜨지 않고 실행됩니다.
# options.add_argument('--window-size= x, y') #실행되는 브라우저 크기를 지정할 수 있습니다.
# options.add_argument('--start-maximized') #브라우저가 최대화된 상태로 실행됩니다.
# options.add_argument('--start-fullscreen') #브라우저가 풀스크린 모드(F11)로 실행됩니다.
# options.add_argument('--blink-settings=imagesEnabled=false') #브라우저에서 이미지 로딩을 하지 않습니다.
# options.add_argument('--mute-audio') #브라우저에 음소거 옵션을 적용합니다.
# options.add_argument('incognito') #시크릿 모드의 브라우저가 실행됩니다.


"""
언제까지 웹드라이버가 기다릴지.
https://selenium-python.readthedocs.io/waits.html
"""

"""
각 종 find 참고.
https://www.geeksforgeeks.org/find_element_by_xpath-driver-method-selenium-python/
"""
# WebDriverWait(self.driver, time).until(EC.element_to_be_clickable((By.CLASS_NAME, class_name)))
class Driver:

    def __init__(self, headless=True) -> None:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        else:
            options.headless = False
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                       options=options)
        self.headless = headless

    def get(self, url:str) -> None:
        self.driver.get(url)

    def get_url_by_category(self, category:str) -> None:
        if category == 'smartwatch':
            self.driver.get("https://search.shopping.naver.com/search/category/100005046?adQuery&catId=50000262&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&spec=M10016843%7CM10664435&timestamp=&viewType=list")

    def wait(self, time:float) -> None:
        self.driver.implicitly_wait(time_to_wait=time)
    
    def wait_until_by_css_selector(self, time:float, class_name:str) -> None:
        WebDriverWait(self.driver, time).until(EC.element_to_be_clickable((By.CSS_SELECTOR, class_name)))
    
    def click(self):
        self.driver.click()
    
    # def find_element_by_xpath(self, element, element_name):
    #     """
    #     XML 형식에 따라 parsing함. 궁금하다면 XML 확인.
    #     """
    #     self.driver.find_element(By.XPATH, "f{element}")

    def release(self):
        self.driver.quit()
        print("DRIVER CLOSING...")




        

category = 'smartwatch'
naver_shopping_driver = Driver(headless=False)

# naver_shopping_driver.wait(20)
naver_shopping_driver.get_url_by_category(category)
# naver_shopping_driver.wait_until_by_css_selector(10, "a[href*='product_link']")
naver_shopping_driver.wait(5)
link = naver_shopping_driver.driver.find_element(By.CSS_SELECTOR, "a[href*='product_link']")
print(link)

naver_shopping_driver.release()
