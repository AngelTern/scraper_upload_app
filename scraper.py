# scraper.py

import os
import time
import json
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

def download_image(url, folder_name, image_name, stop_event=None):
    if stop_event and stop_event.is_set():
        return
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with open(os.path.join(folder_name, image_name), 'wb') as f:
                f.write(response.content)
    except Exception:
        pass

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
        time.sleep(poll_frequency)
        if time.time() > end_time:
            break
    return False

def extract_additional_info_updated(driver, stop_event=None):
    additional_info = {}
    try:
        if stop_event and stop_event.is_set():
            return additional_info
        container = driver.find_element(By.CLASS_NAME, "sc-1b705347-0.hoeUnZ")
        wet_point_container = container.find_elements(By.CLASS_NAME, "sc-1b705347-1.brMFse")[0]
        wet_point = wet_point_container.find_element(By.TAG_NAME, "h3").text if wet_point_container.find_elements(By.TAG_NAME, "h3") else 'N/A'
        additional_info["სველი წერტილი"] = wet_point
        condition_container = container.find_elements(By.CLASS_NAME, "sc-1b705347-1.brMFse")[1]
        condition = condition_container.find_element(By.TAG_NAME, "h3").text if condition_container.find_elements(By.TAG_NAME, "h3") else 'N/A'
        additional_info["მდგომარეობა"] = condition
        status_container = container.find_elements(By.CLASS_NAME, "sc-1b705347-1.brMFse")[2]
        status = status_container.find_element(By.TAG_NAME, "h3").text if status_container.find_elements(By.TAG_NAME, "h3") else 'N/A'
        additional_info["სტატუსი"] = status
    except Exception:
        pass
    return additional_info

def extract_breadcrumbs(driver, stop_event=None):
    breadcrumbs_data = {}
    try:
        if stop_event and stop_event.is_set():
            return breadcrumbs_data
        breadcrumb_container = driver.find_element(By.CLASS_NAME, "sc-3e6bc6bd-20.emoNi")
        breadcrumb_links = breadcrumb_container.find_elements(By.TAG_NAME, "a")
        if len(breadcrumb_links) >= 3:
            breadcrumbs_data["category"] = breadcrumb_links[0].text
            breadcrumbs_data["property_type"] = breadcrumb_links[1].text
            breadcrumbs_data["transaction_type"] = breadcrumb_links[2].text
    except Exception:
        pass
    return breadcrumbs_data

def extract_features_info(driver, stop_event=None):
    features_info = {}
    try:
        if stop_event and stop_event.is_set():
            return features_info
        container = driver.find_element(By.CLASS_NAME, "sc-abd90df5-0")
        feature_elements = container.find_elements(By.CLASS_NAME, "sc-abd90df5-1")
        for element in feature_elements:
            if stop_event and stop_event.is_set():
                break
            title = element.find_element(By.TAG_NAME, "h3").text if element.find_elements(By.TAG_NAME, "h3") else 'N/A'
            value = "არა" if "cWzNVx" in element.get_attribute('class') else "კი"
            features_info[title] = value
    except Exception:
        pass
    return features_info

def extract_property_details(driver, stop_event=None):
    details = {}
    try:
        if stop_event and stop_event.is_set():
            return details
        detail_container = driver.find_element(By.CLASS_NAME, "sc-479ccbe-0.iQgmTI")
        detail_elements = detail_container.find_elements(By.CLASS_NAME, "sc-479ccbe-1.fdyrTe")
        for element in detail_elements:
            if stop_event and stop_event.is_set():
                break
            title = element.find_element(By.CLASS_NAME, "sc-6e54cb25-16.ijRIAC").text if element.find_elements(By.CLASS_NAME, "sc-6e54cb25-16.ijRIAC") else 'N/A'
            value = element.find_element(By.CLASS_NAME, "sc-6e54cb25-4.kjoKdz").text if element.find_elements(By.CLASS_NAME, "sc-6e54cb25-4.kjoKdz") else 'N/A'
            if title == "საერთო ფართი":
                details["საერთო ფართი"] = value
            elif title == "ოთახი":
                details["ოთახი"] = value
            elif title == "საძინებელი":
                details["საძინებელი"] = value
            elif title == "სართული":
                if "/" in value:
                    floor, total_floors = value.split("/")
                    details["სართული"] = floor.strip()
                    details["სართულიანობა"] = total_floors.strip()
                else:
                    details["სართული"] = value
                    details["სართულიანობა"] = "N/A"
    except Exception:
        pass
    return details

def run_scraper(url, agency_price, comment="", headless=False, stop_event=None, output_dir=None):
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.maximize_window()

    try:
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        driver.get(url)

        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        ad_id = None
        def get_ad_id():
            nonlocal ad_id
            id_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-3e6bc6bd-19')]/div/span[contains(text(), 'ID -')]")
            if id_elements:
                ad_id = id_elements[0].text.split("-")[-1].strip()
                return True
            return False

        if not custom_wait(driver, get_ad_id, stop_event=stop_event):
            driver.quit()
            return None

        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        save_directory = os.path.join(output_dir, ad_id)
        os.makedirs(save_directory, exist_ok=True)

        ad_title = None
        def get_ad_title():
            nonlocal ad_title
            elements = driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-0.gDYjuA")
            if elements:
                ad_title = elements[0].text
                return True
            return False

        if not custom_wait(driver, get_ad_title, stop_event=stop_event):
            driver.quit()
            return None

        location = None
        number = None
        def get_location():
            nonlocal location, number
            elements = driver.find_elements(By.ID, "address")
            if elements:
                location_full = elements[0].text
                match = re.search(r'(\d+)$', location_full)
                if match:
                    number = match.group(1)
                    location = location_full[:match.start()].strip()
                else:
                    number = ''
                    location = location_full.strip()
                return True
            return False

        if not custom_wait(driver, get_location, stop_event=stop_event):
            driver.quit()
            return None

        images = []
        def get_images():
            nonlocal images
            elements = driver.find_elements(By.CLASS_NAME, "sc-1acce1b7-10.kCJmmf")
            if elements:
                images = [img.get_attribute("src")[:-10] + ".jpg" for img in elements]
                return True
            return False

        if not custom_wait(driver, get_images, stop_event=stop_event):
            driver.quit()
            return None

        images_directory = os.path.join(save_directory, "images")
        os.makedirs(images_directory, exist_ok=True)
        for idx, img_url in enumerate(images, start=1):
            if stop_event and stop_event.is_set():
                driver.quit()
                return None
            download_image(img_url, images_directory, f"{ad_id}_{idx}.jpg", stop_event=stop_event)

        owner_price = None
        def get_owner_price():
            nonlocal owner_price
            elements = driver.find_elements(By.ID, "price")
            if elements:
                owner_price = elements[0].text
                return True
            return False

        if not custom_wait(driver, get_owner_price, stop_event=stop_event):
            driver.quit()
            return None

        def click_show_number():
            try:
                button = driver.find_element(By.XPATH, "//button[contains(text(), 'ნომრის ჩვენება')]")
                button.click()
                return True
            except Exception:
                return False

        custom_wait(driver, click_show_number, stop_event=stop_event)

        phone_number = None
        def get_phone_number():
            nonlocal phone_number
            elements = driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-11.kkDxQl")
            if elements:
                phone_number = elements[0].text
                return True
            return False

        custom_wait(driver, get_phone_number, stop_event=stop_event)

        name = None
        def get_name():
            nonlocal name
            elements = driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-6.eaYTaN")
            if elements:
                name = elements[0].text
                return True
            return False

        if not custom_wait(driver, get_name, stop_event=stop_event):
            driver.quit()
            return None

        description = None
        def get_description():
            nonlocal description
            elements = driver.find_elements(By.CLASS_NAME, "sc-f5b2f014-2.cpLEJS")
            if elements:
                description = elements[0].text
                return True
            return False

        if not custom_wait(driver, get_description, stop_event=stop_event):
            driver.quit()
            return None

        additional_info = extract_additional_info_updated(driver, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        breadcrumbs_data = extract_breadcrumbs(driver, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        features_info = extract_features_info(driver, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        property_details = extract_property_details(driver, stop_event=stop_event)
        if stop_event and stop_event.is_set():
            driver.quit()
            return None

        data = {
            "ad_id": ad_id,
            "ad_title": ad_title,
            "location": location,
            "number": number,
            "images": images,
            "owner_price": owner_price,
            "agency_price": agency_price,
            "phone_number": phone_number,
            "name": name,
            "description": description,
            "comment": comment,
            "property_details": property_details,
            "additional_info": additional_info,
            "breadcrumbs": breadcrumbs_data,
            "features": features_info,
        }

        with open(os.path.join(save_directory, f"{ad_id}.json"), "w", encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        return ad_id

    except Exception:
        return None
    finally:
        driver.quit()
