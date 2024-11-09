# scraper.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import requests
import re
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def download_image(url, folder_name, image_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(os.path.join(folder_name, image_name), 'wb') as f:
                f.write(response.content)
        else:
            print(f"Failed to download {url}: Status code {response.status_code}")
    except Exception as e:
        print(f"Error downloading image {url}: {e}")

def extract_additional_info(driver):
    additional_info = {}
    try:
        container = driver.find_element(By.CLASS_NAME, "sc-abd90df5-0")
        feature_elements = container.find_elements(By.CLASS_NAME, "sc-abd90df5-1")
        for element in feature_elements:
            title = element.find_element(By.TAG_NAME, "h3").text if element.find_elements(By.TAG_NAME, "h3") else 'N/A'
            value = 'Enabled' if 'icon' in element.get_attribute('class') else 'Disabled'
            additional_info[title] = value
    except Exception as e:
        print(f"Error extracting additional info: {e}")
    return additional_info

def extract_features_info(driver):
    features_info = {}
    try:
        container = driver.find_element(By.CLASS_NAME, "sc-abd90df5-0")
        feature_elements = container.find_elements(By.CLASS_NAME, "sc-abd90df5-1")
        for element in feature_elements:
            title = element.find_element(By.TAG_NAME, "h3").text if element.find_elements(By.TAG_NAME, "h3") else 'N/A'
            value = "არა" if "cWzNVx" in element.get_attribute('class') else "კი"
            features_info[title] = value
    except Exception as e:
        print(f"Error extracting features info: {e}")
    return features_info

def extract_breadcrumbs(driver):
    breadcrumbs_data = {}
    try:
        breadcrumb_container = driver.find_element(By.CLASS_NAME, "sc-3e6bc6bd-20.emoNi")
        breadcrumb_links = breadcrumb_container.find_elements(By.TAG_NAME, "a")
        if len(breadcrumb_links) >= 3:
            breadcrumbs_data["category"] = breadcrumb_links[0].text
            breadcrumbs_data["property_type"] = breadcrumb_links[1].text
            breadcrumbs_data["transaction_type"] = breadcrumb_links[2].text
    except Exception as e:
        print(f"Error extracting breadcrumbs: {e}")
    return breadcrumbs_data

def extract_property_details(driver):
    details = {}
    try:
        detail_container = driver.find_element(By.CLASS_NAME, "sc-479ccbe-0.iQgmTI")
        detail_elements = detail_container.find_elements(By.CLASS_NAME, "sc-479ccbe-1.fdyrTe")
        for element in detail_elements:
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
    except Exception as e:
        print(f"Error extracting property details: {e}")
    return details

def extract_additional_info_updated(driver):
    additional_info = {}
    try:
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
    except Exception as e:
        print(f"Error extracting additional info: {e}")
    return additional_info

def run_scraper(url, agency_price, comment="", headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    driver.maximize_window()

    driver.get(url)
    time.sleep(0.5)

    property_details = extract_property_details(driver)

    try:
        id_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'sc-3e6bc6bd-19')]/div/span[contains(text(), 'ID -')]")
        ad_id = id_elements[0].text.split("-")[-1].strip() if id_elements else "N/A"

        save_directory = os.path.join("data", ad_id)
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        ad_title = driver.find_element(By.CLASS_NAME, "sc-6e54cb25-0.gDYjuA").text if driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-0.gDYjuA") else 'N/A'

        location_full = driver.find_element(By.ID, "address").text if driver.find_elements(By.ID, "address") else 'N/A'
        match = re.search(r'(\d+)$', location_full)
        if match:
            number = match.group(1)
            location = location_full[:match.start()].strip()
        else:
            number = ''
            location = location_full.strip()

        images = driver.find_elements(By.CLASS_NAME, "sc-1acce1b7-10.kCJmmf")
        image_links = [img.get_attribute("src")[:-10] + ".jpg" for img in images]
        images_directory = os.path.join(save_directory, "images")
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)
        for idx, img_url in enumerate(image_links, start=1):
            download_image(img_url, images_directory, f"{ad_id}_{idx}.jpg")

        owner_price = driver.find_element(By.ID, "price").text if driver.find_elements(By.ID, "price") else 'N/A'

        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ნომრის ჩვენება')]"))
            )
            button.click()
            time.sleep(0.5)
            phone_number = driver.find_element(By.CLASS_NAME, "sc-6e54cb25-11.kkDxQl").text if driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-11.kkDxQl") else 'N/A'
        except Exception as e:
            print(f"Error finding phone number: {e}")
            phone_number = "N/A"

        name = driver.find_element(By.CLASS_NAME, "sc-6e54cb25-6.eaYTaN").text if driver.find_elements(By.CLASS_NAME, "sc-6e54cb25-6.eaYTaN") else 'N/A'
        description = driver.find_element(By.CLASS_NAME, "sc-f5b2f014-2.cpLEJS").text if driver.find_elements(By.CLASS_NAME, "sc-f5b2f014-2.cpLEJS") else 'N/A'
        additional_info = extract_additional_info_updated(driver)
        breadcrumbs_data = extract_breadcrumbs(driver)
        features_info = extract_features_info(driver)

        data = {
            "ad_id": ad_id,
            "ad_title": ad_title,
            "location": location,
            "number": number,
            "images": image_links,
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

        print("Data successfully saved.")
        return ad_id

    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        driver.quit()
