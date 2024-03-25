# Preview (Product review)
Product review which match product details
---------------
## Crawler work
- How to test
  1. product_link_crawler로 특정 카테코리 url을 넣는다.
  
     Output: product link json 파일이 api_call 디렉토리 안에 생성된다.

     > __디렉토리가 없으면 직접 만들어야 합니다.__
  3. review_crawler로 특정 product link를 가져온다.

     Output: review json 파일이 생성된다.
