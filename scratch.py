items = []
    for p in range(5): # 1페이지부터 5페이지까지임.
        try:
            product_items = driver.find_elements(By.XPATH, "//div[contains(@class, 'product_item_')]") # substring match.        
            for item in product_items:
                item_dict = {
                                "url" : "",
                                "grade": "",
                                'name': "",
                                'lowest_price': "",
                                'review_count': ""
                               }
                
                price = item.find_element(By.XPATH, "//span[contains(@class, 'price_num_')]")
                item_dict['lowest_price'] = price_formatter(price)
                
                grade = item.find_element(By.XPATH, "//span[contains(@class, 'product_grade_')]")
                item_dict['grade'] = grade_formatter(grade)
                
                grade_num = item.find_element(By.XPATH, "//div[contains(@class, 'product_etc_')]/a/em[contains(@class, 'product_num')]")
                
                item_dict['review_count'] = review_count_formatter(grade_num)

               
                a_tag = item.find_element(By.XPATH, "//div[contains(@class, 'product_title_')]/a")
                item_dict['url'] = a_tag.get_attribute('href')
                item_dict['name'] = a_tag.get_attribute('title')

                items.append(item_dict)

            
            product_dict[page] = items if items else ["END"]

            if p < 4:
                driver.go_next_page()
                
        except TimeoutException as e:
            log.info(f"[ERROR] Time out error occured: Couldn't found footer or last page.\n\
                     Error log: {e}")
        except Exception as e:
            log.info(f"[ERROR] Error log: {e}")