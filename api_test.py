
import requests
from bs4 import BeautifulSoup

# XML 데이터를 가져올 URL
url = "https://openapi.naver.com/v1/search/shop.json"

# 서버로부터 데이터 가져오기
response = requests.get(url)

# 응답이 성공적인지 확인
if response.status_code == 200:
    # BeautifulSoup을 사용하여 XML 파싱
    data = response.json()
    print(data)
else:
    print("Failed to retrieve data")
    print(f"response.status_code: {response.status_code}")
    print(response.json())