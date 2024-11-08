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

def run_uploader(username, password, phone_number, ad_id, enter_description=True, headless=False):
    data_folder = os.path.join("data", ad_id)
    json_file_path = os.path.join(data_folder, f"{ad_id}.json")

    if not os.path.exists(json_file_path):
        print("Can't find data file. Exiting.")
        return

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        # 1. Open the website
        driver.get("https://home.ss.ge/ka/udzravi-qoneba/create")

        # 2. Click the login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "sc-8ce7b879-10"))
        )
        login_button.click()

        # 3. Enter username and password, then log in
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(username)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "sc-1c794266-1"))).click()

        # 4. Proceed with uploading steps
        # 7. Select property type
        property_type = data["breadcrumbs"]["property_type"]
        property_div = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[text()='{property_type}']"))
        )
        property_div.click()

        # 8. Select transaction type
        transaction_type = data["breadcrumbs"]["transaction_type"]
        transaction_div = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[text()='{transaction_type}']"))
        )
        transaction_div.click()

        # 9. Upload all images
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
                    time.sleep(1)  # Small delay between each image upload to avoid issues

        # 10. Enter address from JSON and submit the form
        location = data.get("location", "")
        if location:
            address_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.select__input"))
            )
            address_input.click()
            address_input.send_keys(location)
            time.sleep(1)
            address_input.send_keys(Keys.DOWN)
            address_input.send_keys(Keys.ENTER)

        # 11. Select the number of rooms
        rooms = data.get("property_details", {}).get("ოთახი", "")
        if rooms:
            room_div = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{rooms}']"))
            )
            room_div.click()

        # 12. Select the number of bedrooms
        bedrooms = data.get("property_details", {}).get("საძინებელი", "")
        if bedrooms:
            bedroom_div = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='sc-e8a87f7a-0 dMKNFB']/div[@class='sc-e8a87f7a-1 bilVxg'][2]/div[@class='sc-e8a87f7a-3 gdEkZl']/div[@class='sc-e8a87f7a-4 jdtBxj']/div[@class='sc-226b651b-0 kgzsHg']/p[text()='{0}']".format(bedrooms)))
            )
            bedroom_div.click()

        # 13. Enter total area
        total_area = data.get("property_details", {}).get("საერთო ფართი", "")
        if total_area:
            total_area_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "totalArea"))
            )
            total_area_input.clear()
            total_area_input.send_keys(total_area)

        # 14. Enter floor number
        floor = data.get("property_details", {}).get("სართული", "")
        if floor:
            floor_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "floor"))
            )
            floor_input.clear()
            floor_input.send_keys(floor)

        # 15. Enter number of floors
        floors = data.get("property_details", {}).get("სართულიანობა", "")
        if floors:
            floors_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "floors"))
            )
            floors_input.clear()
            floors_input.send_keys(floors)

        # 16. Select bathroom count
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
        time.sleep(0.5)

        # 17. Select property status
        status = data.get("additional_info", {}).get("სტატუსი", "")
        if status:
            status_div = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{status}']"))
            )
            status_div.click()

        # 18. Select condition
        condition = data.get("additional_info", {}).get("მდგომარეობა", "")
        if condition:
            condition_div = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{condition}']"))
            )
            condition_div.click()

        # 19. Select additional features
        features = data.get("features", {})
        if features:
            feature_divs = driver.find_elements(By.XPATH, "//div[@class='sc-226b651b-0 sc-226b651b-1 kgzsHg LZoqF']")
            for feature_div in feature_divs:
                feature_name = feature_div.find_element(By.TAG_NAME, "p").text
                if features.get(feature_name, "") == "კი":
                    feature_div.click()

        # 20. Enter description
        if enter_description:
            description = data.get("description", "")
            if description:
                description_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.sc-4ccf129b-2.blumtp textarea"))
                )
                description_input.clear()
                description_input.send_keys(description)

        # 21. Enter agency price
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
        time.sleep(1)

        # 22. Enter phone number
        phone_number_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='მობილურის ნომერი']"))
        )
        phone_number_input.clear()
        phone_number_input.send_keys(phone_number)
        time.sleep(1)

        # 23. Click continue button
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.sc-1c794266-1.dICGws.btn-next"))
        )
        continue_button.click()

        # Wait for the next page to load or any other necessary actions
        time.sleep(2)

        print("Uploading completed successfully.")

    except Exception as e:
        print(f"An error occurred during uploading: {e}")
    finally:
        # Close the browser
        driver.quit()
