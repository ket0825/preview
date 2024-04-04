#stdlib
import json
import datetime
<<<<<<< HEAD
=======
import os
>>>>>>> 38933f8db30f33a8fd13d57e4ffc23bb05855f3b
# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webelement import WebElement

# custom lib.
from log import Logger 
log = Logger.get_instance()


# 이후 환경 변수로 수정.
PAGE_NUM = 5


def price_formatter(price_element: WebElement) -> str:
    return price_element.text.replace(",", "").replace("원", "")

def grade_formatter(grade_element: WebElement) -> str:
    grade_str = ""
    try:
        grade_blind = grade_element.find_element(By.XPATH, ".//span[@class='blind']")
        grade_str = grade_element.text.replace("\n", "").replace(grade_blind.text, "")
    except:
        grade_str =  grade_element.text
    
    return grade_str

def review_count_formatter(review_count: WebElement) -> str:
    return review_count.text.replace(",", "").replace("\n", "").replace('(', '').replace(')', '')

def test():
    # category = 'smartwatch'
    category = 'extra_battery'
<<<<<<< HEAD
    naver_shopping_driver = Driver(headless=False, active_user_agent=False)
=======
    naver_shopping_driver = Driver(headless=True, active_user_agent=True, get_log=False)
>>>>>>> 38933f8db30f33a8fd13d57e4ffc23bb05855f3b

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
    
    product_dict = {
                        "category": category,
                        'url': naver_shopping_driver.driver.current_url,
                        }
    
    product_dict['start_page'] = naver_shopping_driver.page
    items = []
    for p in range(PAGE_NUM): # 1페이지부터 5페이지까지임.
        try:
            footer = naver_shopping_driver.wait_until_by_xpath(3, ".//div[contains(@class, 'footer_info')]")
            naver_shopping_driver.move_to_element(element=footer)
            
            # 광고는 자동으로 걸러짐.
            product_items = naver_shopping_driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'product_item_')]") # substring match.        
            for item in product_items:
                item_dict = {
                                "url" : "",
                                "grade": "",
                                'name': "",
                                'lowest_price': "",
                                'review_count': "",
                                'brand': "", # 차후 넣을 예정.
                                'maker': "", # 차후 넣을 예정.
                               }
                # 링크와 제품명 추출.
                try:
                    a_tag = item.find_element(By.XPATH, ".//div[contains(@class, 'product_title_')]/a")
                    item_dict['url'] = a_tag.get_attribute('href')
                    item_dict['name'] = a_tag.get_attribute('title')
                    items.append(item_dict)
                except Exception as e:
                    log.error(f'[ERROR] Could not catch product url and name.')

                # 가격 추출.
                try:
                    lowest_price = item.find_element(By.XPATH, ".//span[contains(@class, 'price_num_')]")
                    item_dict['lowest_price'] = price_formatter(lowest_price)
                # 별점 추출.
                except Exception as e:
                    log.error(f'[ERROR] Could not catch price at {item_dict["name"]}')
                try:
                    grade = item.find_element(By.XPATH, ".//span[contains(@class, 'product_grade_')]")
                    item_dict['grade'] = grade_formatter(grade)
                except Exception as e:
                    log.warning(f'[WARNING] Could not catch grade at {item_dict["name"]}')
                # 리뷰 개수 따오기.
                try:
                    grade_num = item.find_element(By.XPATH, ".//div[contains(@class, 'product_etc_')]/a/em[contains(@class, 'product_num')]")
                    # grade_num = product_etc.find_element(By.XPATH, ".//em[contains(@class, 'product_num')]")
                    item_dict['review_count'] = review_count_formatter(grade_num)
                except Exception as e:
                    log.warning(f'[WARNING] Could not catch grade_num at {item_dict["name"]}')

                
            if p < PAGE_NUM - 1:
                naver_shopping_driver.go_next_page()
                
        except TimeoutException as e:
            log.info(f"[ERROR] Time out error occured: Couldn't found footer or last page.\n\
                     Error log: {e}")
        except Exception as e:
            log.info(f"[ERROR] Error log: {e}")

    product_dict['end_page'] = naver_shopping_driver.page
    product_dict['items'] = items

    current_time = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm')
<<<<<<< HEAD
=======
    if not os.path.exists("./api_call"):
        os.mkdir("./api_call")
    
>>>>>>> 38933f8db30f33a8fd13d57e4ffc23bb05855f3b
    with open(f'./api_call/{current_time}_{category}_product_link.json', 'w', encoding='utf-8-sig') as json_file:
        json.dump(product_dict, json_file, ensure_ascii=False)
        log.info(f"[SUCCESS] Success at {category}")

    
    naver_shopping_driver.release()


if __name__ == '__main__':
    test()



