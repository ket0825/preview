# Preview (Product review) project
- 제품 리뷰와 OCR를 크롤링합니다

- Honeycomb과 결합하여 작동합니다 (https://github.com/ket0825/honeycomb)
---------------

## 예시

![a](https://github.com/user-attachments/assets/97f299fa-d4af-49cf-b1f7-7d3cda4c010a)
------------
![b](https://github.com/user-attachments/assets/d792df1d-c277-426a-8b02-d16ec92cae27)
------------
![c](https://github.com/user-attachments/assets/54b2d3ee-98f0-4b27-bd73-2f03634091d2)


## 구성요소
### Driver
- 프록시 IP가 있다면 사용할 수 있습니다
- User Agent를 바꿀 수 있습니다
- IP 밴에 대한 Failover 프로세스가 있습니다
------------------------------

### Route handler
- 리트라이 패턴과 에러 핸들링을 통하여 웹서버에 데이터를 넘깁니다
- 데이터를 패칭할 웹서버를 설정할 수 있습니다
------------------------------

### Image processing
- PaddleOCR을 사용하여 판매자의 제품 설명 데이터를 가져옵니다
- 큰 이미지 사이즈 때문에 글자가 잘리지 않도록 이미지를 잘라서 OCR을 수행합니다
- 멀티프로세싱 사용을 고려중입니다
  
-------------------------------

### GUI

- tkinter를 위한 GUI 레이블링 툴입니다
  1. OCR tagging
     - OCR 데이터 레이블링 툴입니다
  2. Review tagging
     - 리뷰 데이터 레이블링 툴입니다
-------------------------------

### 크롤러는 아래와 같이 작동합니다
  1. product_link_crawler.py
     - 카테고리별 네이버 가격비교 탭에서 작동합니다
     - 제품 링크, 리뷰 수, 제품명 등을 가져옵니다

       
  2. review_crawler.py
     - Crawling at the product-unit price comparison page.
     - 네이버 가격비교 제품별 크롤링을 진행합니다
     - OCR 데이터를 가져와 PaddleOCR로 분석합니다
     - 크롬드라이버의 네트워크 부분에서 리뷰 데이터를 json으로 가져옵니다
     - 네이버가 제공하는 스펙 데이터를 가져옵니다


---------------------------------

### Dockerfile (product_link_crawler.py만 가능합니다) 
