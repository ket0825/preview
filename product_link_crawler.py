#stdlib
import json
import datetime
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


# custom lib.
from log import Logger 
log = Logger.get_instance()

xhr_pattern = r"XMLHttpRequest"

def test():
    # category = 'smartwatch'
    category = 'extra_battery'
    naver_shopping_driver = Driver(headless=False, active_user_agent=False)

    # 태그 매치
    """https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
    # XPATH 예시들.
    """https://selenium-python.readthedocs.io/locating-elements.html"""
    # XPATH substring match.
    # link = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')/a]") 
    # username = driver.find_element(By.XPATH, "//form[input/@name='username']")
    # CSS_SELECTOR substring match.
    # link = naver_shopping_driver.driver.find_elements(By.CSS_SELECTOR, "div[class*='reviewItems_title']") # substring match.
    
    naver_shopping_driver.get_url_by_category(category)
    naver_shopping_driver.wait(5)
    
    page_links_dict = {category: naver_shopping_driver.driver.current_url}
    page_links_dict['start_page'] = naver_shopping_driver.page
    
    for p in range(5): # 1페이지부터 5페이지까지임.
        try:
            footer = naver_shopping_driver.wait_until_by_xpath(3, "//div[contains(@class, 'footer_info')]")
            naver_shopping_driver.move_to_element(element=footer)
            page = naver_shopping_driver.page
            
            # 광고는 자동으로 걸러짐.
            a_tags = naver_shopping_driver.driver.find_elements(By.XPATH, "//div[contains(@class, 'product_title_')]/a") # substring match.
            hrefs = []
            for a_tag in a_tags:
                link = a_tag.get_attribute('href')
                # log.info(f"link: {a_tag.get_attribute('href')}")
                hrefs.append(link)
            
            page_links_dict[page] = hrefs if hrefs else ["END"]

            if p < 4:
                naver_shopping_driver.go_next_page()
                
        except TimeoutException as e:
            log.info(f"[ERROR] Time out error occured: {e}")
        except Exception as e:
            log.info(f"[ERROR] Unknownrror occured: {e}")
        
    page_links_dict['end_page'] = naver_shopping_driver.page

    current_time = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm')
    with open(f'./api_call/{current_time}_{category}_product_link.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(page_links_dict, json_file, ensure_ascii=False)
        log.info(f"[SUCCESS] Success at {category}")


    
    naver_shopping_driver.release()


if __name__ == '__main__':
    test()



