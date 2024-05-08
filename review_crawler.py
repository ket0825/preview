# 태그 매치
"""https://saucelabs.com/resources/blog/selenium-tips-css-selectors"""
# XPATH 예시들.
"""https://selenium-python.readthedocs.io/locating-elements.html"""

#stdlib
import json
import time
import random
import datetime
import re
import os
from argparse import ArgumentParser

# 3rd party lib.
from driver.driver import Driver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

# custom lib.
from log import Logger 
from image_processing.ocr_engine import OCREngine
from image_processing.image_function_main import char_pix_extract, make_ocr_sequence
from route_handler.route_handler import RouteHandler


log = Logger.get_instance()
route_handler = RouteHandler()

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
        match_nv_mids = [item['match_nv_mid'] for item in product_raw_json['items']]
        return links, product_names, category, match_nv_mids


def ocr_function(src):
    cut_pix_list = char_pix_extract(src)    
    return make_ocr_sequence(src, cut_pix_list)


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

def get_image_specs(driver:Driver, xpath):
    """
    Get image specs with xpath.
    """
    web_elements = driver.driver.find_elements(By.XPATH, xpath)
    img_spec = []
    for web_element in web_elements:
        src = web_element.get_attribute('src')
        # .gif, 동영상 등의 확장자를 막기 위함.
        if '.jpg' not in src and '.png' not in src:
            continue

        driver.move_to_element(web_element)
        time.sleep(3)

        img_spec_dict = {
            'img_url': "",
            'img_loc': [],
            'img_rendered_size':[],
            'ocr':[{'text': "", 'bbox': []}]
        }

        img_spec_dict['img_url'] = src
        img_spec_dict['img_loc'] = [web_element.location['x'], web_element.location['y']]
        img_spec_dict['img_rendered_size'] = [web_element.size['width'], web_element.size['height']]
        img_spec_dict['ocr'] = ocr_function(src)
        img_spec.append(img_spec_dict)
    
    return img_spec

# TODO: later, it should be an multiprocessing.
def fetch_product_details(driver:Driver):
    spec_info_section = driver.driver.find_element(By.XPATH, ".//h3[contains(@class, 'specInfo_section_title__')]")
    driver.move_to_element(element=spec_info_section)

    # html tag에 height가 있는데...?
    naver_spec =  {} # 둘 중 하나임.
    seller_spec =  []
    
    
    # 본 컨텐츠는 ... 부분 위치.
    try:
        driver.wait_until_by_xpath(3, ".//p[contains(@class, 'imageSpecInfo_provide_')]")
    except:
        try:
            driver.wait_until_by_xpath(3, ".//p[contains(@class, 'specInfo_provide_')]") # 이미지 스펙 없는 경우.
        except TimeoutException:
            log.info(f"[WARNING] There is no product details.")
    

    

    # 일반적인 이미지 스펙 추출 가능한지 확인.
    try:
        driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'imageSpecInfo_export_')]")
    except:
        # 안되면 naver spec.
        log.info(f"[INFO] No export spec at here.")
        try:
            tables = driver.driver.find_elements(By.XPATH, ".//div[contains(@class, 'attribute_product_attribute_')]/table")
            for table in tables:
                table_rows = table.find_elements(By.XPATH, ".//tr")
                for row in table_rows:
                    keys = row.find_elements(By.XPATH, ".//th")
                    vals = row.find_elements(By.XPATH, ".//td")
                    for key, val in zip(keys, vals):
                        naver_spec[key.text] = {
                                            'text': val.text, 
                                            'location': [val.location['y'], val.location['x']]
                                            }
        except:
            log.info(f"[WARNING] There is no product details.")
                
    # brand content banner 존재 시.
    # TODO: # 사진 가져오고, 이후 병렬처리 (multiprocessing)    
    try:
        seller_spec.extend(get_image_specs(driver, ".//div[contains(@class, 'brandContent_export_')]/img"))
    except NoSuchElementException:
        pass
    # except Exception as e:
    #     log.info(f"[ERROR] Can't get url. Error: {e}")
        
    # 일반 img spec 존재 시.
    try:
        seller_spec.extend(get_image_specs(driver, ".//p[contains(@id, 'detailFromBrand')]/img"))                
    except NoSuchElementException:        
        pass


    return naver_spec, seller_spec


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
    keys_to_remove = ["aidaCreateTime", "esModifyTime", "modifyDate", "pageUrl", "registerDate", "imageCount", "imageYn", "images", "mallProductId", "mallReviewId", "rankScore", "title", "videoCount", "videoYn", "videos", "mallLogoUrl"]
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


def review_crawler(category:str, type:str,
                    headless=False, 
                    active_user_agent=False, 
                    use_proxy=False) -> None:
    
    naver_shopping_driver = Driver(headless=headless, active_user_agent=active_user_agent, use_proxy=use_proxy, get_log=True)        
    
    # s_category_row = route_handler.get_category(s_category=category)
    # caid = s_category_row[0]['caid']    

    # products = route_handler.get_product(caid=caid)

    product_links, product_names, category, match_nv_mids = get_links("./api_call/20240402_04h11m_keyboard_product_link.json")
    
    # flag = False
    for link, name, match_nv_mid in zip(product_links, product_names, match_nv_mids):
        # 원래는 크롤링한 사이트 링크들.
        # if flag or name == "데이비드테크 엔보우 N패드 네오":
        #     flag = True
        # else:
        #     continue

        
        naver_shopping_driver.get(link) 
        # TODO: test cases:
        # 디알고 헤드셋. 적은 평점.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/36974003618?adId=nad-a001-02-000000223025435&channel=nshop.npla&cat_id=%EB%94%94%EC%A7%80%ED%84%B8/%EA%B0%80%EC%A0%84&NaPm=ct%3Dlu2l3ulc%7Cci%3D0zW0003ypdPztN%5FoFfjw%7Ctr%3Dpla%7Chk%3Dc6b52bbfde6b3967102cd5b772f10fb97a2d3356&cid=0zW0003ypdPztN_oFfjw")
        # 어프어프. 리뷰 없음.
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/45960130619?&NaPm=ct%3Dludqbeyg%7Cci%3Dc6cf7cf700e756c885e4e7e9829c11d935a7e990%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3Dbc572d7cb475be323262c78ba2bdd1074c1f6d81")
        # 로지텍 K830: 리뷰 27000개
        # naver_shopping_driver.get("https://search.shopping.naver.com/catalog/8974763652?&NaPm=ct%3Dlucr5xuw%7Cci%3D5549087459ddae34d93daf8f0d9e0686cf56ea87%7Ctr%3Dslcc%7Csn%3D95694%7Chk%3D784343aaa845130bbe75468952f58e847fc0499c")

        # naver_shopping_driver.wait_until_by_css_selector(3)
        try:
            floating_tabs = naver_shopping_driver.wait_until_by_xpath(10, ".//div[contains(@class, 'floatingTab_detail_tab')]")
        except:
            if naver_shopping_driver.driver.find_element(By.XPATH, ".//div[contains(@class, 'content_error')]"):
                log.warning("[WARNING] IP Blocked.")
                return
                # 이후 prodxy ip 바꿔서 naver_shopping_driver 다시 얻어야 함.


        # 브랜드 insert.
        brand, maker = fetch_brand_maker(naver_shopping_driver)
        log.info(f"[INFO] Brand: {brand}, Maker: {maker}")
        
        # 제품 상세 보러가기
        product_details = floating_tabs.find_elements(By.XPATH, ".//li")[1]
        naver_shopping_driver.move_to_element(element=product_details)
        product_details.click()

        # 제품 상세 더보기 있는 경우와 없는 경우 둘 다 있음.
        try:
            btn_detail_more = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'imageSpecInfo_btn_detail_more')]")
            naver_shopping_driver.move_to_element(element=btn_detail_more)
            btn_detail_more.click()
        except:
            log.warning("[WARNING] No see more button.")
        
        # 제품 상세에서 ocr 및 location 따기. 이건 상황에 따라...
        # naver_spec, seller_spec = fetch_product_details(naver_shopping_driver)
        # with open('specs.json', 'a', encoding='utf-8-sig') as json_file:
        #     json.dump({"naver_spec": naver_spec, "seller_spec": seller_spec}, json_file, ensure_ascii=False)

        # 제품 네이버 스펙 보러가기.
        spec = fetch_spec(naver_shopping_driver)            
        log.info(f"[INFO] Spec: {spec}")            

        # 리뷰 크롤링하기.
        review_filters = naver_shopping_driver.driver.find_elements(By.XPATH, ".//ul[contains(@class, 'filter_top_list_')]/li")
        review_filters.pop(0) # 필터 중 전체 별점 제거.
        
        # 필요 없는 log 제거.
        flush_log(naver_shopping_driver)

        # 리뷰가 없는 제품인 경우. 스킵함.
        try:
            sort_by_recent = naver_shopping_driver.wait_until_by_xpath(3, ".//a[contains(@class, 'filter_sort') and contains(@data-nclick, 'rec')]") # recent라는 뜻임.
        except Exception as e:
            log.warning(f"[WARNING] No Reviews in {name}. Go to next product.")
            continue


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

                    naver_shopping_driver.move_to_element(element=review_page)
                    review_page.click()

                    try:
                        # 100 페이지를 넘어가려고 하면 경고가 나옴.
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
            if not os.path.exists("./reviews"):
                os.mkdir("./reviews")

            with open(f'./reviews/{current_time}_{category}_{name}_review.json', 'w', encoding='utf-8-sig') as json_file:
                log.info("Review data from JSON file completed.")
                json.dump(total_reviews, json_file, ensure_ascii=False)
            
            total_reviews.clear()
        
        log.info(f"[SUCCESS] {name} crawled complete.")


    naver_shopping_driver.release()


if __name__ == '__main__':    
    parser = ArgumentParser(description='Review crawler for naver shopping. Enter the category.')
    parser.add_argument('category', type=str, help='Enter the category you want to crawl.', default="keyboard")
    parser.add_argument('--headless', type=bool, help='Set headless mode.', default=False)
    parser.add_argument('--use_proxy', type=bool, help='Set use proxy ip.', default=False)
    parser.add_argument('--active_user_agent', type=bool, help='Active user agent.', default=False)
    parser.add_argument('--type', type=str, help='Enter the type.', default="R0")

    args = parser.parse_args() 

    log.info(f"[INFO] Start crawling at {args.category}")
    log.info(f"[INFO] Headless: {args.headless}, Use proxy: {args.use_proxy}, Active user agent: {args.active_user_agent}")
    review_crawler(category=args.category, headless=args.headless, 
                         active_user_agent=args.active_user_agent, 
                         use_proxy=args.use_proxy,
                         type=args.type)    
    log.info(f"[SUCCESS] Success at {args.category}")
    
    




