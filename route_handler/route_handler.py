import requests
from log import Logger
from settings import STAGE, URL, REVIEW_URL, OCR_URL
from typing import List, Dict
import json

log = Logger.get_instance()
DEBUG = True

def delete_request(url, timeout=1):
    retry_count = 0
    if DEBUG:
        retry_count = 4
        log.info("DEBUG MODE")
        
    while retry_count < 5:
        try:
            res = requests.delete(url, timeout=timeout)
            if res.status_code:
                return res.text, res.status_code
        except requests.exceptions.Timeout as e:
            log.error(f'[ERROR] Timeout at {url}. Retry count: {retry_count}')
            retry_count += 1
        except requests.exceptions.RequestException as e:
            log.error(f'[ERROR] Error at {url}.\nError log: {e}')
            return None, None
    
    log.info(f'[ERROR] Could not delete request at {url}. Retry count: {retry_count}')
    return None, None

def post_request(url, data, timeout=1):
    retry_count = 0
    for k, v in data.items():
        if not v:
            data[k] = None
            
    if DEBUG:
        retry_count = 4
        log.info("DEBUG MODE")

    while retry_count < 5:
        try:
            res = requests.post(url, json=data, timeout=timeout)
            if res.status_code:
                return res.text, res.status_code
        except requests.exceptions.Timeout as e:
            log.error(f'[ERROR] Timeout at {url}. Retry count: {retry_count}')
            retry_count += 1
        except requests.exceptions.RequestException as e:
            log.error(f'[ERROR] Error at {url}.\nError log: {e}')
            return None, None
        except Exception as e: # Response is not json
            log.error(f'[ERROR] Error at {url}.\nError log: {res}')
            retry_count += 1
            return None
    
    log.info(f'[ERROR] Could not post request at {url}. Retry count: {retry_count}')
    return None, None

def get_request(url, data, timeout=1):
    retry_count = 0
    if DEBUG:
        retry_count = 4
        log.info("DEBUG MODE")
        
    while retry_count < 5:
        try:
            res = requests.get(url, json=data, timeout=timeout)
            if res:                
                return res.json()
        except requests.exceptions.Timeout as e:
            log.error(f'[ERROR] Timeout at {url}. Retry count: {retry_count}')
            retry_count += 1
        except requests.exceptions.RequestException as e:
            log.error(f'[ERROR] Error at {url}.\nError log: {e}')
            retry_count += 1
            return None
        except Exception as e: # Response is not json
            log.error(f'[ERROR] Error at {url}.\nError log: {res}')
            retry_count += 1
            return None
        
    log.info(f'[ERROR] Could not post request at {url}. Retry count: {retry_count}')
    return None

class RouteHandler:
    _stage = STAGE
    
    def __init__(self) -> None:                                
        log.info(f'[INFO] RouteHandler initialized. STAGE: {self.__class__._stage}')
        if self.__class__._stage == 'prod':
            log.info(f"[INFO] Production mode...")                    
            self._url = URL
            log.info(f"[INFO] URL: {self._url}")            
            self._review_url = REVIEW_URL
            log.info(f"[INFO] REVIEW_URL: {self._review_url}")            
            self._ocr_url = OCR_URL
            log.info(f"[INFO] OCR_URL: {self._ocr_url}")
        elif self.__class__._stage == 'local':
            log.info(f"[INFO] Local mode...")
            self._url = URL
            log.info(f"[INFO] URL: {self._url}")            
            self._review_url = REVIEW_URL
            self._ocr_url = OCR_URL
            log.info(f"[INFO] REVIEW_URL: {self._review_url}")
        else:
            log.warning(f"[WARNING] ELSE mode...")
            self._url = URL
            self._review_url = REVIEW_URL
        
    def get_ip(self, unused=True):
        res = get_request(url=f'{self._url}/ip?unused={unused}', data=None, timeout=1)        
        return res        
    
    def upsert_ip(self, data):
        res_text, res_code = post_request(f'{self._url}/ip', data)
        return res_text, res_code
    
    def delete_ip(self, address):
        res_text, res_code = delete_request(url=f'{self._url}/ip/{address}', timeout=1)
        return res_text, res_code
    
    def get_product(self, prid=None, match_nv_mid=None, s_category=None, caid=None):
        """
        prid: path parameter
        name: query string
        s_category: query string (by join)
        caid: query string
        """
        url = f'{self._url}/product'
        suffix_url = ''
        if prid and isinstance(prid, str):
            suffix_url += f'/{prid}'
        if match_nv_mid and isinstance(match_nv_mid, str):
            suffix_url += f'?match_nv_mid={match_nv_mid}&'

        if caid and isinstance(caid, str):
            suffix_url += f'?caid={caid}&'
        elif s_category and isinstance(s_category, str):
            suffix_url += f'?s_category={s_category}&'
        suffix_url = suffix_url.rstrip('&')
        res = get_request(url=f"{url}{suffix_url}", data=None, timeout=100)
        
        return res
        
    
    def upsert_product_match(self, data:Dict): # First result at crawling.
        res_text, res_code = post_request(f'{self._url}/product/match', data, timeout=30)
        if res_code == 400:
            log.info(f'[ERROR] {res_text}, data: {data}')
        return res_text, res_code

    def update_product_detail_one(self, data:Dict):
        """
        data: SINGLE PRODUCT PACKET:
        {
            "name": "string",
            "url": "string",
            "lowest_price": "string",
            review_count
            match_nv_mid
            #
            "brand": "string",
            "maker": "string",
            "naver_spec": JSON,
            "seller_spec": JSON,
            #
            detail_image_urls
            ...
        }
        """
        res_text, res_code = post_request(f'{self._ocr_url}', data=data, timeout=10)
        if res_code == 400:
            log.info(f'[ERROR] {res_text}, data: {data}')

        return res_text, res_code

    def get_product_history(self, caid=None, prid=None, count_desc=None):
        """
        caid: query string
        prid: query string
        count_desc: query string
        """
        url = f'{self._url}/product_history'
        suffix_url = ''
        if caid and isinstance(caid, str):
            suffix_url += f'?caid={caid}&'
        if prid and isinstance(prid, str):
            suffix_url += f'?prid={prid}&'
        if count_desc and isinstance(count_desc, int):
            suffix_url += f'?count_desc={count_desc}&'
        suffix_url = suffix_url.rstrip('&')            
        res = get_request(url=f'{url}{suffix_url}', data=None, timeout=1)
        
        return res
        
    
    def get_category(self, caid=None, s_category=None, m_cateogry=None):
        """
        caid: path parameter
        s_category: query string
        m_category: query string
        """
        url = f'{self._url}/category'
        suffix_url = ''
        if caid and isinstance(caid, str):
            suffix_url += f'/{caid}'
        if s_category and isinstance(s_category, str):
            suffix_url += f'?s_category={s_category}&'
        if m_cateogry and isinstance(m_cateogry, str):
            suffix_url += f'?m_cateogry={m_cateogry}&'
        suffix_url = suffix_url.rstrip('&')            
        res = get_request(url=f'{url}{suffix_url}', data=None, timeout=5)
        
        return res
        
    
    def upsert_category(self, data):
        """
        data: List of category packet
        [
            {
            "s_category": "string",
            "m_category": "string",
            "category_url": "string"
            "s_topic": "list",
            "m_topic": "list",
            "type": "C0",
            },
            ...
        ]
        """
        res_text, res_code = post_request(f'{self._url}/category', data, timeout=5)
        return res_text, res_code
    
    def get_review(self, caid, prid=None, reid=None):
        """
        caid: path parameter
        prid: query string
        reid: query string
        """
        url = f'{self._url}/review'
        suffix_url = ''        
        suffix_url += f'/{caid}'
        if prid and isinstance(prid, str):
            suffix_url += f'?prid={prid}&'
        if reid and isinstance(reid, str):
            suffix_url += f'?reid={reid}&'
        suffix_url = suffix_url.rstrip('&')            
        res = get_request(url=f'{url}{suffix_url}', data=None, timeout=3)
        
        return res
    
    def check_if_need_update(self, data:Dict)-> List:
        """
        check if need to update review data

        Args:
            data (Dict): id to aida_modify_time
        """
        url = f'{self._url}/review/need_update'
        
        assert isinstance(data, dict), f'[ERROR] data should be dict. data: {data}'        
        
        res_text, res_code = post_request(url, data, timeout=3)
        log.info(f'[INFO] res_text: {res_code}')
        return json.loads(res_text)
        
        
    
    def upsert_review_batch(self, data):
        """
        data: dict of  packet
        {
            'type': type,
            'category': s_category,
            'prid': prid,
            'match_nv_mid': match_nv_mid,        
            'reviews': [{            
            "content": "string",
            ...
            },
            ...,            
            ]
        }
        """
        
        res_text, res_code = post_request(f'{self._review_url}', data, timeout=1000)        
        if res_code == 400:
            log.info(f'[ERROR] {res_text}, data: {data}')
            
        return res_text, res_code
    
    def get_topic_by_type(
            self, type, caid=None, reid=None, 
            prid=None, topic_code=None, 
            topic_score=None,  
            positive_yn=None, sentiment_scale=None                                                                  
        ):
        """
        reid: path parameter
        topic_code: query string
        type: query string
        positive_yn: query string
        sentiment_scale: query string
        """
        url = f'{self._url}/topic'
        suffix_url = '?'

        if reid and isinstance(reid, str):
            suffix_url += f'reid={reid}&'
        if caid and isinstance(caid, str):
            suffix_url += f'caid={caid}&'
        if prid and isinstance(prid, str):
            suffix_url += f'prid={prid}&'
        if topic_code and isinstance(topic_code, str):
            suffix_url += f'topic_code={topic_code}&'
        if topic_score and isinstance(topic_score, str):
            suffix_url += f'topic_score={topic_score}&'    
        if type and isinstance(type, str):
            suffix_url += f'type={type}&'
        if positive_yn and isinstance(positive_yn, str):
            suffix_url += f'positive_yn={positive_yn}&'
        if sentiment_scale and isinstance(sentiment_scale, str):
            suffix_url += f'sentiment_scale={sentiment_scale}&'
        suffix_url = suffix_url.rstrip('&')
        
        print(f'{url}{suffix_url}')
        res = get_request(url=f'{url}{suffix_url}', data=None, timeout=5)
        
        return res
    
        
    def get_kano_model_data(self, type, caid):
        """
        type: query string
        caid: query string
        """
        url = f'{self._url}/topic/kano_model'
        suffix_url = '?'
        if type and isinstance(type, str):
            suffix_url += f'type={type}&'
        if caid and isinstance(caid, str):
            suffix_url += f'caid={caid}&'
        suffix_url = suffix_url.rstrip('&')            
        res = get_request(url=f'{url}{suffix_url}', data=None, timeout=10)
        
        return res
        


if __name__ == "__main__":
    route_handler = RouteHandler()
    print(route_handler.get_topic_by_type(type="RT0", caid="C02"))


    

