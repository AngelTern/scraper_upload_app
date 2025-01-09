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
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.keys import Keys
import logging

logging.basicConfig(
    filename=os.path.join(os.getcwd(), 'uploader.log'),
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

def custom_wait(driver, condition_function, timeout=10, poll_frequency=0.5, stop_event=None):
    """
    Custom wait function that tries condition_function repeatedly
    up to 'timeout' seconds, sleeping 'poll_frequency' between tries.
    If stop_event is set, it aborts early.
    """
    print(f"[custom_wait] Starting custom wait for up to {timeout} seconds.")
    end_time = time.time() + timeout
    while True:
        if stop_event and stop_event.is_set():
            print("[custom_wait] Stop event detected. Exiting wait.")
            return False
        try:
            if condition_function():
                print("[custom_wait] Condition satisfied before timeout.")
                return True
        except Exception:
            pass
        if stop_event and stop_event.wait(poll_frequency):
            print("[custom_wait] Stop event triggered during wait.")
            return False
        if time.time() > end_time:
            print("[custom_wait] Timed out waiting for condition.")
            break
    return False

def click_element(driver, locator, stop_event=None):
    """
    Wait up to 10s to find and click an element by locator.
    """
    def condition():
        element = driver.find_element(*locator)
        print(f"[click_element] Clicking element located by {locator}.")
        element.click()
        return True
    print(f"[click_element] Attempting to find and click {locator} within 10s.")
    return custom_wait(
        driver,
        condition_function=condition,
        timeout=10,
        poll_frequency=0.5,
        stop_event=stop_event
    )

def send_keys_to_element(driver, locator, keys, stop_event=None):
    """
    Wait up to 10s to find an element by locator and send keys to it.
    """
    def condition():
        element = driver.find_element(*locator)
        print(f"[send_keys_to_element] Sending keys '{keys}' to element located by {locator}.")
        element.clear()
        element.send_keys(keys)
        return True
    print(f"[send_keys_to_element] Attempting to send keys '{keys}' to {locator} within 10s.")
    return custom_wait(
        driver,
        condition_function=condition,
        timeout=10,
        poll_frequency=0.5,
        stop_event=stop_event
    )

def indefinite_click_next(driver, locator, stop_event=None):
    """
    Indefinitely try to find and click 'Next' button.
    The user might be navigating pages manually, so this won't
    time out. It only returns when the button is successfully clicked.
    """
    print("[indefinite_click_next] Starting indefinite loop to find & click Next button.")
    while True:
        if stop_event and stop_event.is_set():
            print("[indefinite_click_next] Stop event detected. Exiting loop.")
            return False

        try:
            next_button = driver.find_element(*locator)
            print("[indefinite_click_next] Next button found. Clicking it now.")
            next_button.click()
            time.sleep(1.0)
            print("[indefinite_click_next] Next button clicked successfully.")
            return True
        except (NoSuchElementException, ElementClickInterceptedException):
            print("[indefinite_click_next] Next button not found or not clickable yet. Retrying...")
            time.sleep(0.5)
        except Exception as e:
            print(f"[indefinite_click_next] Error while clicking Next button: {e}")
            time.sleep(0.5)

def wait_for_final_element_indefinitely(driver, locator, stop_event=None):
    """
    Indefinitely wait for the final element (e.g., a "Finish" button) to appear.
    Once found, click it, retrieve the final URL from the clipboard, and return it.

    If the final element doesn't appear right away,
    this loop continues until the user triggers stop_event or the element is found.
    """
    print("[wait_for_final_element_indefinitely] Starting indefinite loop to wait for final element.")
    while True:
        if stop_event and stop_event.is_set():
            print("[wait_for_final_element_indefinitely] Stop event detected. Exiting loop.")
            return None

        time.sleep(0.5)
        try:
            final_button = driver.find_element(*locator)
            print("[wait_for_final_element_indefinitely] Final element found. Clicking it now.")
            final_button.click()
            time.sleep(1.0)
            final_url = pyperclip.paste()
            if final_url:
                print("[wait_for_final_element_indefinitely] Final URL found in clipboard.")
                return final_url
            else:
                print("[wait_for_final_element_indefinitely] Clicked final element but clipboard is empty.")
        except NoSuchElementException:
            print("[wait_for_final_element_indefinitely] Final element not found yet. Retrying...")
        except Exception as e:
            print(f"[wait_for_final_element_indefinitely] Error while waiting for final element: {e}")

def run_uploader(username, password, phone_number, ad_id,
                 enter_description=True, headless=False,
                 stop_event=None, output_dir=None):
    """
    Automates the upload flow on home.ss.ge based on scraped JSON data.
    """
    print("[run_uploader] Starting run_uploader function.")
    if output_dir is None:
        logging.error("Output directory not provided to run_uploader.")
        print("[run_uploader] Output directory not provided.")
        return None

    # Prepare paths
    data_folder = os.path.join(output_dir, ad_id)
    json_file_path = os.path.join(data_folder, f"{ad_id}.json")
    logging.info(f"Uploader looking for JSON file at: {json_file_path}")
    print(f"[run_uploader] Looking for JSON file at: {json_file_path}")

    if not os.path.exists(json_file_path):
        logging.error(f"JSON file not found at: {json_file_path}")
        print("[run_uploader] JSON file not found. Exiting.")
        return None

    # Load scraped data
    print("[run_uploader] Loading scraped JSON data.")
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logging.info("JSON data loaded successfully.")
            print("[run_uploader] JSON data loaded successfully.")
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        print("[run_uploader] JSON decode error encountered. Exiting.")
        return None
    except Exception as e:
        logging.error(f"Error reading JSON file: {e}")
        print(f"[run_uploader] Error reading JSON file: {e}")
        return None

    # Chrome options
    print(f"[run_uploader] Setting up Chrome with headless={headless}")
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

    # Launch browser
    print("[run_uploader] Launching Chrome browser.")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
    driver.maximize_window()
    final_url = None

    try:
        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event detected before any navigation.")
            driver.quit()
            return None

        print("[run_uploader] Navigating to main create page: https://home.ss.ge/ka/udzravi-qoneba/create")
        driver.get("https://home.ss.ge/ka/udzravi-qoneba/create")

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event detected after navigation. Quitting.")
            driver.quit()
            return None

        print("[run_uploader] Clicking login locator.")
        login_locator = (By.CLASS_NAME, "sc-8ce7b879-10")
        if not click_element(driver, login_locator, stop_event=stop_event):
            print("[run_uploader] Could not click login button. Exiting.")
            driver.quit()
            return None

        print("[run_uploader] Entering credentials.")
        if not send_keys_to_element(driver, (By.NAME, "email"), username, stop_event=stop_event):
            print("[run_uploader] Could not enter email. Exiting.")
            driver.quit()
            return None
        if not send_keys_to_element(driver, (By.NAME, "password"), password, stop_event=stop_event):
            print("[run_uploader] Could not enter password. Exiting.")
            driver.quit()
            return None

        print("[run_uploader] Submitting login form.")
        submit_locator = (By.CSS_SELECTOR, "button.sc-1c794266-1.cFcCnt")
        if not click_element(driver, submit_locator, stop_event=stop_event):
            print("[run_uploader] Could not submit login. Exiting.")
            driver.quit()
            return None

        print("[run_uploader] Checking for 'Add New' button.")
        add_new_button_path = (By.CSS_SELECTOR, "div.sc-b3bd94d2-0.kmSDJX > button.sc-1c794266-1.eqszNP")
        add_new_button_element = driver.find_elements(*add_new_button_path)
        if add_new_button_element:
            print("[run_uploader] 'Add New' button found, attempting to click it.")
            if not click_element(driver, add_new_button_path, stop_event=stop_event):
                print("[run_uploader] Could not click 'Add New' button. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event detected after login. Quitting.")
            driver.quit()
            return None

        # Click property type
        property_type = data.get("breadcrumbs", {}).get("property_type")
        if property_type:
            print(f"[run_uploader] Clicking property type: {property_type}")
            property_locator = (By.XPATH, f"//div[text()='{property_type}']")
            if not click_element(driver, property_locator, stop_event=stop_event):
                print("[run_uploader] Could not click property type. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event detected after property type. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Click transaction type
        transaction_type = data.get("breadcrumbs", {}).get("transaction_type")
        if transaction_type:
            print(f"[run_uploader] Clicking transaction type: {transaction_type}")
            transaction_locator = (By.XPATH, f"//div[text()='{transaction_type}']")
            if not click_element(driver, transaction_locator, stop_event=stop_event):
                print("[run_uploader] Could not click transaction type. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after transaction type. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Upload images
        image_folder = os.path.join(data_folder, "images")
        if os.path.exists(image_folder):
            image_paths = [
                os.path.abspath(os.path.join(image_folder, img))
                for img in os.listdir(image_folder)
                if img.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            if image_paths:
                print("[run_uploader] Found image files. Attempting to upload.")
                for image_path in image_paths:
                    if stop_event and stop_event.is_set():
                        print("[run_uploader] Stop event while uploading images.")
                        driver.quit()
                        return None
                    try:
                        image_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                        print(f"[run_uploader] Uploading image {image_path}")
                        image_input.send_keys(image_path)
                        if stop_event and stop_event.wait(0.5):
                            print("[run_uploader] Stop event triggered during image upload wait.")
                            driver.quit()
                            return None
                    except Exception as e:
                        logging.warning(f"Could not upload image {image_path}: {e}")
                        print(f"[run_uploader] WARNING: Could not upload image {image_path}: {e}")

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event detected after image uploads.")
            driver.quit()
            return None

        # Enter location if any
        location = data.get("location", "")
        if location:
            print(f"[run_uploader] Setting location: {location}")
            address_locator = (By.CSS_SELECTOR, "input#react-select-3-input.select__input")
            if not send_keys_to_element(driver, address_locator, location, stop_event=stop_event):
                print("[run_uploader] Could not enter location. Exiting.")
                driver.quit()
                return None
            if stop_event and stop_event.wait(0.5):
                print("[run_uploader] Stop event triggered while setting location.")
                driver.quit()
                return None
            # Press down + enter in location dropdown
            try:
                address_input = driver.find_element(*address_locator)
                address_input.send_keys(Keys.DOWN)
                address_input.send_keys(Keys.ENTER)
                print("[run_uploader] Pressed down+enter to select location from dropdown.")
            except Exception as e:
                logging.warning(f"Failed to select location from dropdown: {e}")
                print(f"[run_uploader] WARNING: Failed to select location from dropdown: {e}")
        time.sleep(0.5)
        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after setting location. Quitting.")
            driver.quit()
            return None

        # House number if any
        number = data.get("number")
        if number:
            print(f"[run_uploader] Entering house number: {number}")
            number_input_locator = (
                By.CSS_SELECTOR,
                "#create-app-loc > div.sc-bb305ae5-3.iDHOHS > div.sc-bb305ae5-4.VxicA > "
                "div:nth-child(2) > label > div > input"
            )
            if not send_keys_to_element(driver, number_input_locator, number, stop_event=stop_event):
                print("[run_uploader] Could not set house number. Exiting.")
                driver.quit()
                return None
        time.sleep(0.5)

        # Rooms
        rooms = data.get("property_details", {}).get("ოთახი", "")
        if rooms:
            print(f"[run_uploader] Selecting rooms: {rooms}")
            rooms_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{rooms}']")
            if not click_element(driver, rooms_locator, stop_event=stop_event):
                print("[run_uploader] Could not click rooms element. Exiting.")
                driver.quit()
                return None
        time.sleep(0.5)
        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after selecting rooms. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Bedrooms
        bedrooms = data.get("property_details", {}).get("საძინებელი", "")
        if bedrooms:
            print(f"[run_uploader] Selecting bedrooms: {bedrooms}")
            bedrooms_locator = (
                By.XPATH,
                f"//div[@class='sc-e8a87f7a-0 dMKNFB']/div[@class='sc-e8a87f7a-1 bilVxg'][2]"
                f"/div[@class='sc-e8a87f7a-3 gdEkZl']/div[@class='sc-e8a87f7a-4 jdtBxj']"
                f"/div[@class='sc-226b651b-0 kgzsHg']/p[text()='{bedrooms}']"
            )
            if not click_element(driver, bedrooms_locator, stop_event=stop_event):
                print("[run_uploader] Could not click bedrooms element. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after bedrooms. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Total Area
        total_area = data.get("property_details", {}).get("საერთო ფართი", "")
        if total_area:
            print(f"[run_uploader] Setting total area: {total_area}")
            total_area_locator = (By.NAME, "totalArea")
            if not send_keys_to_element(driver, total_area_locator, total_area, stop_event=stop_event):
                print("[run_uploader] Could not set total area. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after total area. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Floor
        floor = data.get("property_details", {}).get("სართული", "")
        if floor:
            print(f"[run_uploader] Setting floor: {floor}")
            floor_locator = (By.NAME, "floor")
            if not send_keys_to_element(driver, floor_locator, floor, stop_event=stop_event):
                print("[run_uploader] Could not set floor. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after setting floor. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Floors
        floors = data.get("property_details", {}).get("სართულიანობა", "")
        if floors:
            print(f"[run_uploader] Setting floors: {floors}")
            floors_locator = (By.NAME, "floors")
            if not send_keys_to_element(driver, floors_locator, floors, stop_event=stop_event):
                print("[run_uploader] Could not set floors. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after setting floors. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Bathroom count
        bathroom_count = data.get("additional_info", {}).get("სველი წერტილი", "")
        if bathroom_count:
            print(f"[run_uploader] Selecting bathroom count: {bathroom_count}")
            try:
                bathroom_section = driver.find_element(By.ID, "create-app-details")
                container_div = bathroom_section.find_element(By.CLASS_NAME, "sc-e8a87f7a-0.dMKNFB")
                specific_div = container_div.find_elements(By.CLASS_NAME, "sc-e8a87f7a-1.bilVxg")[6]
                gdEkZl_div = specific_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-3.gdEkZl")
                jdtBxj_div = gdEkZl_div.find_element(By.CLASS_NAME, "sc-e8a87f7a-4.jdtBxj")
                bathroom_divs = jdtBxj_div.find_elements(By.CLASS_NAME, "sc-226b651b-0.kgzsHg")
                for div in bathroom_divs:
                    if stop_event and stop_event.is_set():
                        print("[run_uploader] Stop event during bathroom selection. Quitting.")
                        driver.quit()
                        return None
                    if div.find_element(By.TAG_NAME, "p").text == bathroom_count:
                        print("[run_uploader] Clicking matching bathroom count.")
                        div.click()
                        break
            except Exception as e:
                logging.warning(f"Failed to set bathroom count: {e}")
                print(f"[run_uploader] WARNING: Failed to set bathroom count: {e}")

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after bathroom count. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Status
        status = data.get("additional_info", {}).get("სტატუსი", "")
        if status:
            print(f"[run_uploader] Selecting status: {status}")
            status_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{status}']")
            if not click_element(driver, status_locator, stop_event=stop_event):
                print("[run_uploader] Could not click status element. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after status selection. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Condition
        condition = data.get("additional_info", {}).get("მდგომარეობა", "")
        if condition:
            print(f"[run_uploader] Selecting condition: {condition}")
            condition_locator = (By.XPATH, f"//div[@class='sc-226b651b-0 kgzsHg']/p[text()='{condition}']")
            if not click_element(driver, condition_locator, stop_event=stop_event):
                print("[run_uploader] Could not click condition element. Exiting.")
                driver.quit()
                return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after condition selection. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Features
        features = data.get("features", {})
        if features:
            print("[run_uploader] Attempting to select feature checkboxes.")
            feature_divs = driver.find_elements(By.XPATH, "//div[@class='sc-226b651b-0 sc-226b651b-1 kgzsHg LZoqF']")
            for feature_div in feature_divs:
                if stop_event and stop_event.is_set():
                    print("[run_uploader] Stop event while selecting features. Quitting.")
                    driver.quit()
                    return None
                feature_name = feature_div.find_element(By.TAG_NAME, "p").text
                if features.get(feature_name, "") == "კი":
                    try:
                        print(f"[run_uploader] Clicking feature: {feature_name}")
                        feature_div.click()
                    except Exception as e:
                        logging.warning(f"Could not click feature {feature_name}: {e}")
                        print(f"[run_uploader] WARNING: Could not click feature {feature_name}: {e}")

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after features. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Description
        if enter_description:
            description = data.get("description", "")
            if description:
                print(f"[run_uploader] Entering description. Length: {len(description)} chars.")
                description_locator = (By.CSS_SELECTOR, "div.sc-4ccf129b-2.blumtp textarea")
                if not send_keys_to_element(driver, description_locator, description, stop_event=stop_event):
                    print("[run_uploader] Could not enter description. Exiting.")
                    driver.quit()
                    return None

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after description. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Agency price
        agency_price = data.get("agency_price", "")
        if agency_price:
            print(f"[run_uploader] Setting agency price: {agency_price}")
            try:
                agency_price_div = driver.find_element(By.ID, "create-app-price")
                container_div = agency_price_div.find_element(By.CLASS_NAME, "sc-9c9d017-2.jKKqhD")
                labels = container_div.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    if stop_event and stop_event.is_set():
                        print("[run_uploader] Stop event while setting agency price. Quitting.")
                        driver.quit()
                        return None
                    if "active" not in label.get_attribute("class"):
                        label.click()
                        agency_price_input = label.find_element(By.TAG_NAME, "input")
                        agency_price_input.clear()
                        agency_price_input.send_keys(agency_price)
                        print("[run_uploader] Agency price entered successfully.")
                        break
            except Exception as e:
                logging.warning(f"Could not set agency price: {e}")
                print(f"[run_uploader] WARNING: Could not set agency price: {e}")

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after agency price. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        '''# Phone number
        if phone_number:
            print(f"[run_uploader] Entering phone number: {phone_number}")
            phone_number_locator = (By.CSS_SELECTOR, "input[placeholder='მობილურის ნომერი']")
            if not send_keys_to_element(driver, phone_number_locator, phone_number, stop_event=stop_event):
                print("[run_uploader] Could not enter phone number. Exiting.")
                driver.quit()
                return None'''

        if stop_event and stop_event.is_set():
            print("[run_uploader] Stop event after phone number. Quitting.")
            driver.quit()
            return None
        time.sleep(0.5)

        # Indefinitely click "Next"
        print("[run_uploader] Will now attempt to click the 'Next' button indefinitely.")
        next_button_locator = (By.CSS_SELECTOR, "button.btn-next")
        indefinite_click_next(driver, next_button_locator, stop_event=stop_event)

        print("[run_uploader] Indefinite next-click finished. Possibly user navigated further manually.")

        # Indefinitely wait for final element & get final URL
        final_element_locator = (
            By.CSS_SELECTOR,
            "#__next > div.sc-af3cf45-0.fWBmkz > div.sc-af3cf45-6.ijmwBP > button.hBiInR"
        )
        print("[run_uploader] Will now wait indefinitely for the final element to appear.")
        final_url = wait_for_final_element_indefinitely(driver, final_element_locator, stop_event=stop_event)
        if final_url:
            print(f"[run_uploader] Final URL retrieved: {final_url}")
        else:
            print("[run_uploader] Final URL not retrieved (stop event or element never appeared).")

        return final_url

    except Exception as e:
        logging.error(f"Error occurred in run_uploader: {e}", exc_info=True)
        print(f"[run_uploader] EXCEPTION: {e}")
        return None
    finally:
        print("[run_uploader] Quitting driver.")
        driver.quit()
