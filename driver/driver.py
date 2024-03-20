from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from log import Logger
log = Logger.get_instance()

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
# 느긋하게 하려면 options.set_capability("pageLoadStrategy"... 이 부분 주석처리.
class Driver:
    
    def __init__(self, headless=True) -> None:
        # TODO: start from log requests.
        # make chrome log requests
        # capabilities = DesiredCapabilities.CHROME
        # capabilities["loggingPrefs"] = {"performance": "ALL"}  # newer: goog:loggingPrefs
        options, capa = self.set_options(headless)
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                    #    desired_capabilities=capa,
                                       options=options)
        self.headless = headless
    
    def set_options(self, headless=False) -> None:
        options = Options()
        if headless:
            options.add_argument("--headless=new")

        options.add_argument('--mute-audio')
        options.add_argument("--disable-gpu") 
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--no-sandbox")
        # options.add_argument("--blink-settings=imagesEnabled=false") # Image Disable
        options.add_argument('--disable-blink-features=AutomationControlled')    # Automation detection disable
        preferences = {
            "profile.default_content_setting_values.notifications": 2, # prevent web cookie notification
            "webrtc.ip_handling_policy" : "disable_non_proxied_udp", # prevent IP leak issues.
            "webrtc.multiple_routes_enabled": False, # prevent IP leak issues.
            "webrtc.nonproxied_udp_enabled" : False # prevent IP leak issues.
        }
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) # automation message exclude.
        options.add_experimental_option('useAutomationExtension', False) 
        options.add_experimental_option("prefs", preferences)    # Add Preferences
        capa = DesiredCapabilities.CHROME
        options.set_capability("pageLoadStrategy", 'none') # does not wait loading.
        options.set_capability("acceptInsecureCerts", True)
        # capa["pageLoadStrategy"] = "none" # does not wait loading.
        # capa['acceptInsecureCerts'] = True
        # capa['acceptSslCerts'] = True
        return options, capa

    def get(self, url:str) -> None:
        self.driver.get(url)

    def get_url_by_category(self, category:str) -> None:
        self.page = 1
        if category == 'smartwatch':
            self.driver.get(f"https://search.shopping.naver.com/search/category/100005046?adQuery&catId=50000262&origQuery&pagingIndex={self.page}&pagingSize=40&productSet=model&query&sort=rel&spec=M10016843%7CM10664435&timestamp=&viewType=list")
    
    def get_current_url(self):
        return self.driver.current_url
    
    def go_next_page(self):
        if self.driver.current_url:
            url = self.driver.current_url.replace(f"pagingIndex={self.page}", f"pagingIndex={self.page+1}")
            self.driver.get(url)
            log.info(f"[MOVED] GO TO NEXT PAGE: {self.page} -> {self.page+1}")
            self.page +=1
        else:
            log.error("[ERROR] no current URL.")


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
    
    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    def release(self):
        self.driver.quit()
        print("DRIVER CLOSING...")