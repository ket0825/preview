import requests
import json

def request_product_match():    
    with open('./api_call/20240402_04h11m_keyboard_product_link_new.json', 'r', encoding="utf-8-sig") as f:
        data = json.load(f)

    res = requests.post('http://localhost:5000/api/product/match', json=data)
    print(res.text, res.status_code)  



if __name__ == '__main__':
    request_product_match()
