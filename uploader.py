# uploader.py

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException

def click_element(driver, locator, retries=3):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(locator))
            element.click()
            return
        except StaleElementReferenceException:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            else:
                raise
        except Exception:
            raise

def send_keys_to_element(driver, locator, keys, retries=3):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator))
            element.clear()
            element.send_keys(keys)
            return
        except StaleElementReferenceException:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            else:
                raise
        except Exception:
            raise

def run_uploader(username, password, phone_number, ad_id, enter_description=True, headless=False):
    data_folder = os.path.join("data", ad_id)
    json_file_path = os.path.join(data_folder, f"{ad_id}.json")

    if not os.path.exists(json_file_path):
        return None

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    driver.maximize_window()

    final_url = None  

    try:
        driver.get("https://home.ss.ge/ka/udzravi-qoneba/create")

        login_locator = (By.CLASS_NAME, "sc-8ce7b879-10")
        click_element(driver, login_locator)

        send_keys_to_element(driver, (By.NAME, "email"), username)
        send_keys_to_element(driver, (By.NAME, "password"), password)

        submit_locator = (By.CSS_SELECTOR, "button.sc-1c794266-1.cFcCnt")
        click_element(driver, submit_locator)

        #If previous attempt failed
        add_new_button_path = (By.CSS_SELECTOR, "div.sc-b3bd94d2-0.kmSDJX > button.sc-1c794266-1.eqszNP")
        add_new_button_element = driver.find_elements(*add_new_button_path)
        
        if add_new_button_element:
            click_element(driver, add_new_button_path)
        
        '''previously_added_unsusccesfully = (By.CSS_SELECTOR, "div.sc-b3bd94d2-0.kmSDJX")
        elements = driver.find_elements(*previously_added_unsusccesfully)

        if elements:
            add_new_button = (By.CSS_SELECTOR, 'button[class="sc-1c794266-1 eqszNP"]')
            click_element(driver, add_new_button)'''

        
        property_type = data["breadcrumbs"]["property_type"]
        property_locator = (By.XPATH, f"//div[text()='{property_type}']")
        click_element(driver, property_locator)

        transaction_type = data["breadcrumbs"]["transaction_type"]
        transaction_locator = (By.XPATH, f"//div[text()='{transaction_type}']")
        click_element(driver, transaction_locator)

        image_folder = os.path.join(data_folder, "images")
        if os.path.exists(image_folder):
            image_paths = [
                os.path.abspath(os.path.join(image_folder, img))
                for img in os.listdir(image_folder)
                if img.endswith((".png", ".jpg", ".jpeg"))
            ]
            if image_paths:
                for image_path in image_paths:
                    image_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    image_input.send_keys(image_path)
                    time.sleep(1) 

        location = data.get("location", "")
        if location:
            address_locator = (By.CSS_SELECTOR, "input.select__input:nth-of-type(2)")
            send_keys_to_element(driver, address_locator, location)
            time.sleep(1)
            address_input = driver.find_element(*address_locator)
            address_input.send_keys(Keys.DOWN)
            address_input.send_keys(Keys.ENTER)

        rooms = data.get("property_details", {}).get("ოთახი", "")
        if rooms:
            rooms_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{rooms}']")
            click_element(driver, rooms_locator)

        bedrooms = data.get("property_details", {}).get("საძინებელი", "")
        if bedrooms:
            bedrooms_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{bedrooms}']")
            click_element(driver, bedrooms_locator)

        total_area = data.get("property_details", {}).get("საერთო ფართი", "")
        if total_area:
            total_area_locator = (By.NAME, "totalArea")
            send_keys_to_element(driver, total_area_locator, total_area)

        floor = data.get("property_details", {}).get("სართული", "")
        if floor:
            floor_locator = (By.NAME, "floor")
            send_keys_to_element(driver, floor_locator, floor)

        floors = data.get("property_details", {}).get("სართულიანობა", "")
        if floors:
            floors_locator = (By.NAME, "floors")
            send_keys_to_element(driver, floors_locator, floors)

        bathroom_count = data.get("additional_info", {}).get("სველი წერტილი", "")
        if bathroom_count:
            bathroom_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "create-app-details"))
            )
            container_div = bathroom_section.find_element(By.CLASS_NAME, "sc-e8a87f7a-0.dMKNFB")
            specific_div = container_div.find_elements(By.CLASS_NAME, "sc-e8a87f7a-1.bilVxg")[6]
            gdEkZl_div = specific_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-3.gdEkZl")
            jdtBxj_div = gdEkZl_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-4.jdtBxj")
            bathroom_divs = jdtBxj_div.find_elements(By.CLASS_NAME, "sc-226b651b-0.kgzsHg")
            for div in bathroom_divs:
                if div.find_element(By.TAG_NAME, "p").text == bathroom_count:
                    div.click()
                    break
        time.sleep(1)

        status = data.get("additional_info", {}).get("სტატუსი", "")
        if status:
            status_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{status}']")
            click_element(driver, status_locator)

        condition = data.get("additional_info", {}).get("მდგომარეობა", "")
        if condition:
            condition_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{condition}']")
            click_element(driver, condition_locator)

        features = data.get("features", {})
        if features:
            feature_divs = driver.find_elements(By.XPATH, "//div[@class='sc-226b651b-0 sc-226b651b-1 kgzsHg LZoqF']")
            for feature_div in feature_divs:
                feature_name = feature_div.find_element(By.TAG_NAME, "p").text
                if features.get(feature_name, "") == "კი":
                    try:
                        feature_div.click()
                    except Exception:
                        pass  

        if enter_description:
            description = data.get("description", "")
            if description:
                description_locator = (By.CSS_SELECTOR, "div.sc-4ccf129b-2.blumtp textarea")
                send_keys_to_element(driver, description_locator, description)

        agency_price = data.get("agency_price", "")
        if agency_price:
            agency_price_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "create-app-price"))
            )
            container_div = agency_price_div.find_element(By.CLASS_NAME, "sc-9c9d017-2.jKKqhD")
            labels = container_div.find_elements(By.TAG_NAME, "label")
            for label in labels:
                if "active" not in label.get_attribute("class"):
                    label.click()
                    time.sleep(0.5)
                    agency_price_input = label.find_element(By.TAG_NAME, "input")
                    agency_price_input.clear()
                    agency_price_input.send_keys(agency_price)
                    break
        time.sleep(100000)

        if phone_number:
            phone_number_locator = (By.CSS_SELECTOR, "input[placeholder='მობილურის ნომერი']")
            send_keys_to_element(driver, phone_number_locator, phone_number)

        continue_button_locator = (By.CSS_SELECTOR, "button.sc-1c794266-1.dICGws.btn-next")
        click_element(driver, continue_button_locator)

        time.sleep(2)

        final_url = driver.current_url

        return final_url  

    except Exception:
        return None
    finally:
        driver.quit()
