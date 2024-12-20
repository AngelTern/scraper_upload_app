# uploader.py

import os
import time
import json
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import logging


logging.basicConfig(
    filename=os.path.join(os.getcwd(), 'uploader.log'),
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def custom_wait(driver, condition_function, timeout=10, poll_frequency=0.5, stop_event=None):
    end_time = time.time() + timeout
    while True:
        if stop_event and stop_event.is_set():
            return False
        try:
            if condition_function():
                return True
        except Exception:
            pass
        if stop_event and stop_event.wait(poll_frequency):
            return False
        if time.time() > end_time:
            break
    return False

def click_element(driver, locator, stop_event=None):
    def condition():
        element = driver.find_element(*locator)
        element.click()
        return True
    return custom_wait(driver, condition_function=condition, timeout=10, poll_frequency=0.5, stop_event=stop_event)

def send_keys_to_element(driver, locator, keys, stop_event=None):
    def condition():
        element = driver.find_element(*locator)
        element.clear()
        element.send_keys(keys)
        return True
    return custom_wait(driver, condition_function=condition, timeout=10, poll_frequency=0.5, stop_event=stop_event)

def run_uploader(username, password, phone_number, ad_id, enter_description=True, headless=False, stop_event=None, output_dir=None):
    if output_dir is None:
        logging.error("Output directory not provided to run_uploader.")
        return None
    print(output_dir)
    data_folder = os.path.join(output_dir, ad_id)
    json_file_path = os.path.join(data_folder, f"{ad_id}.json")
    logging.info(f"Uploader looking for JSON file at: {json_file_path}")
    print(json_file_path)

    if not os.path.exists(json_file_path):
        logging.error(f"JSON file not found at: {json_file_path}")
        return None

    with open(json_file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            logging.info("JSON data loaded successfully.")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None

    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    final_url = None

    try:
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        driver.get("https://home.ss.ge/ka/udzravi-qoneba/create")

        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        login_locator = (By.CLASS_NAME, "sc-8ce7b879-10")
        if not click_element(driver, login_locator, stop_event=stop_event):
            driver.quit()
            return None

        if not send_keys_to_element(driver, (By.NAME, "email"), username, stop_event=stop_event):
            driver.quit()
            return None
        if not send_keys_to_element(driver, (By.NAME, "password"), password, stop_event=stop_event):
            driver.quit()
            return None

        submit_locator = (By.CSS_SELECTOR, "button.sc-1c794266-1.cFcCnt")
        if not click_element(driver, submit_locator, stop_event=stop_event):
            driver.quit()
            return None

        add_new_button_path = (By.CSS_SELECTOR, "div.sc-b3bd94d2-0.kmSDJX > button.sc-1c794266-1.eqszNP")
        add_new_button_element = driver.find_elements(*add_new_button_path)
        if add_new_button_element:
            if not click_element(driver, add_new_button_path, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        property_type = data["breadcrumbs"]["property_type"]
        property_locator = (By.XPATH, f"//div[text()='{property_type}']")
        if not click_element(driver, property_locator, stop_event=stop_event):
            driver.quit()
            return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        transaction_type = data["breadcrumbs"]["transaction_type"]
        transaction_locator = (By.XPATH, f"//div[text()='{transaction_type}']")
        if not click_element(driver, transaction_locator, stop_event=stop_event):
            driver.quit()
            return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        image_folder = os.path.join(data_folder, "images")
        if os.path.exists(image_folder):
            image_paths = [
                os.path.abspath(os.path.join(image_folder, img))
                for img in os.listdir(image_folder)
                if img.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            if image_paths:
                for image_path in image_paths:
                    if stop_event and stop_event.is_set():
                        driver.quit()
                        return None
                    try:
                        image_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                        image_input.send_keys(image_path)
                        if stop_event and stop_event.wait(0.5):
                            driver.quit()
                            return None
                    except Exception:
                        pass

        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        location = data.get("location", "")
        if location:
            address_locator = (By.CSS_SELECTOR, "input#react-select-3-input.select__input")
            if not send_keys_to_element(driver, address_locator, location, stop_event=stop_event):
                driver.quit()
                return None
            if stop_event and stop_event.wait(0.5):
                driver.quit()
                return None
            address_input = driver.find_element(*address_locator)
            address_input.send_keys(Keys.DOWN)
            address_input.send_keys(Keys.ENTER)
        time.sleep(0.5)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        number = data.get("number", "")
        if number:
            number_input_locator = (By.CSS_SELECTOR, "#create-app-loc > div.sc-bb305ae5-3.iDHOHS > div.sc-bb305ae5-4.VxicA > div:nth-child(2) > label > div > input")
            if not send_keys_to_element(driver, number_input_locator, number, stop_event=stop_event):
                driver.quit()
                return None
        time.sleep(0.5)
        rooms = data.get("property_details", {}).get("ოთახი", "")
        #print(rooms)
        if rooms:
            rooms_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{rooms}']")
            if not click_element(driver, rooms_locator, stop_event=stop_event):
                driver.quit()
                return None
        time.sleep(0.5)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        bedrooms = data.get("property_details", {}).get("საძინებელი", "")
        #print(bedrooms)
        if bedrooms:
            
            bedrooms_locator = (By.XPATH, f"//div[@class='sc-e8a87f7a-0 dMKNFB']/div[@class='sc-e8a87f7a-1 bilVxg'][2]/div[@class='sc-e8a87f7a-3 gdEkZl']/div[@class='sc-e8a87f7a-4 jdtBxj']/div[@class='sc-226b651b-0 kgzsHg']/p[text()='{bedrooms}']")
            if not click_element(driver, bedrooms_locator, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        total_area = data.get("property_details", {}).get("საერთო ფართი", "")
        if total_area:
            total_area_locator = (By.NAME, "totalArea")
            if not send_keys_to_element(driver, total_area_locator, total_area, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        floor = data.get("property_details", {}).get("სართული", "")
        if floor:
            floor_locator = (By.NAME, "floor")
            if not send_keys_to_element(driver, floor_locator, floor, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        floors = data.get("property_details", {}).get("სართულიანობა", "")
        if floors:
            floors_locator = (By.NAME, "floors")
            if not send_keys_to_element(driver, floors_locator, floors, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        bathroom_count = data.get("additional_info", {}).get("სველი წერტილი", "")
        if bathroom_count:
            try:
                bathroom_section = driver.find_element(By.ID, "create-app-details")
                container_div = bathroom_section.find_element(By.CLASS_NAME, "sc-e8a87f7a-0.dMKNFB")
                specific_div = container_div.find_elements(By.CLASS_NAME, "sc-e8a87f7a-1.bilVxg")[6]
                gdEkZl_div = specific_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-3.gdEkZl")
                jdtBxj_div = gdEkZl_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-4.jdtBxj")
                bathroom_divs = jdtBxj_div.find_elements(By.CLASS_NAME, "sc-226b651b-0.kgzsHg")
                for div in bathroom_divs:
                    if stop_event and stop_event.is_set():
                        driver.quit()
                        return None
                    if div.find_element(By.TAG_NAME, "p").text == bathroom_count:
                        div.click()
                        break
            except Exception:
                pass

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        status = data.get("additional_info", {}).get("სტატუსი", "")
        if status:
            status_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{status}']")
            if not click_element(driver, status_locator, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        condition = data.get("additional_info", {}).get("მდგომარეობა", "")
        if condition:
            condition_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{condition}']")
            if not click_element(driver, condition_locator, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        features = data.get("features", {})
        if features:
            feature_divs = driver.find_elements(By.XPATH, "//div[@class='sc-226b651b-0 sc-226b651b-1 kgzsHg LZoqF']")
            for feature_div in feature_divs:
                if stop_event and stop_event.is_set():
                    driver.quit()
                    return None
                feature_name = feature_div.find_element(By.TAG_NAME, "p").text
                if features.get(feature_name, "") == "კი":
                    try:
                        feature_div.click()
                    except Exception:
                        pass

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        if enter_description:
            description = data.get("description", "")
            if description:
                description_locator = (By.CSS_SELECTOR, "div.sc-4ccf129b-2.blumtp textarea")
                if not send_keys_to_element(driver, description_locator, description, stop_event=stop_event):
                    driver.quit()
                    return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        agency_price = data.get("agency_price", "")
        if agency_price:
            try:
                agency_price_div = driver.find_element(By.ID, "create-app-price")
                container_div = agency_price_div.find_element(By.CLASS_NAME, "sc-9c9d017-2.jKKqhD")
                labels = container_div.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    if stop_event and stop_event.is_set():
                        driver.quit()
                        return None
                    if "active" not in label.get_attribute("class"):
                        label.click()
                        agency_price_input = label.find_element(By.TAG_NAME, "input")
                        agency_price_input.clear()
                        agency_price_input.send_keys(agency_price)
                        break
            except Exception:
                pass

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        if phone_number:
            phone_number_locator = (By.CSS_SELECTOR, "input[placeholder='მობილურის ნომერი']")
            if not send_keys_to_element(driver, phone_number_locator, phone_number, stop_event=stop_event):
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        continue_button_locator = (By.CSS_SELECTOR, "button.sc-1c794266-1.dICGws.btn-next")
        if not click_element(driver, continue_button_locator, stop_event=stop_event):
            driver.quit()
            return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None
        time.sleep(0.5)
        final_element_locator = (By.CSS_SELECTOR, "#__next > div.sc-af3cf45-0.fWBmkz > div.sc-af3cf45-6.ijmwBP > button.sc-1c794266-1.hBiInR")
        
        def wait_for_final_element_and_click():
            while not stop_event.is_set():
                try:
                    element = driver.find_element(*final_element_locator)
                    element.click()
                    if stop_event and stop_event.wait(1):
                        driver.quit()
                        return None
                    final_url = pyperclip.paste()
                    if final_url:
                        return final_url
                except NoSuchElementException:
                    pass
                except Exception as e:
                    print(f"Error waiting for final element: {e}")
                if stop_event and stop_event.wait(1):
                    driver.quit()
                    return None
            return None

        final_url = wait_for_final_element_and_click()

        return final_url

    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        driver.quit()
