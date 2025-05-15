import time
import cv2
import pytesseract
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\urvashi.aggarwal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://rera.punjab.gov.in/reraindex/publicview/projectinfo")

# ✅ Enter Registration Number
reg_input = driver.find_element(By.ID, "Input_RegdProject_RERAnumberRegistration")  
reg_input.send_keys("PBRERA-BTI08-PC0292")  # Example registration number

# ✅ Find CAPTCHA refresh button
refresh_button = driver.find_element(By.CLASS_NAME, "capcha-refresh")

# ✅ Retry CAPTCHA up to 5 times
max_attempts = 5
attempt = 0

while attempt < max_attempts:
    attempt += 1
    print(f"\n🔄 Attempt {attempt} of {max_attempts}")

    # ✅ Wait for CAPTCHA to Load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "capcha-badge")))
    captcha_element = driver.find_element(By.CLASS_NAME, "capcha-badge")

    # ✅ Take Screenshot of CAPTCHA
    captcha_element.screenshot("captcha.png")
    print("📸 Screenshot taken for CAPTCHA.")

    # ✅ Process CAPTCHA Image for OCR
    image = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # Improve clarity
    cv2.imwrite("processed_captcha.png", thresh)  # Save processed image for debugging

    # ✅ Extract CAPTCHA Text using OCR
    raw_captcha_text = pytesseract.image_to_string(thresh, config="--psm 6").strip()
    print("🔍 Raw OCR Output:", raw_captcha_text)

    # ✅ Ensure CAPTCHA is exactly 6 characters long
    captcha_text = raw_captcha_text.replace(" ", "")  # Remove spaces
    if len(captcha_text) == 6:  
        print("✅ Valid CAPTCHA Extracted:", captcha_text)
    else:
        print("❌ OCR Failed: Extracted CAPTCHA is invalid. Refreshing CAPTCHA...")
        refresh_button.click()  # Click the refresh button
        time.sleep(2)  # Wait for new CAPTCHA to load
        continue  # Retry with new CAPTCHA

    # ✅ Enter CAPTCHA Text
    captcha_input = driver.find_element(By.ID, "Input_RegdProject_CaptchaText")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)

    # ✅ Click Search Button
    search_button = driver.find_element(By.ID, "btn_SearchProjectSubmit")
    driver.execute_script("arguments[0].click();", search_button)

    # ✅ Wait for results
    time.sleep(5)

    # ✅ Check for CAPTCHA failure pop-up
    try:
        pop_up = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "confirm")))
        print("⚠️ Invalid CAPTCHA detected. Clicking OK and retrying...")
        pop_up.click()  # Click "OK" button to retry
        time.sleep(2)  # Short delay before retrying
        refresh_button.click()  # Click refresh to get a new CAPTCHA
        time.sleep(2)  # Wait for new CAPTCHA
    except:
        print("🎉 CAPTCHA Accepted! Proceeding...")
        break  # No pop-up means CAPTCHA was correct

# ✅ Click the "View" button
try:
    print("\n🔍 Waiting for 'View' button to appear...")
    view_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "modalOpenerButtonRegdProject"))
    )
    print("✅ 'View' button found! Clicking now...")
    driver.execute_script("arguments[0].click();", view_button)
except:
    print("❌ 'View' button not found or not clickable. Exiting.")
    driver.quit()
    exit()

# ✅ Wait for the new page to load
time.sleep(5)

# ✅ Click the "Project Details" tab
try:
    print("\n🔍 Waiting for 'Project Details' tab...")
    project_details_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='#Projects']"))
    )
    print("✅ 'Project Details' tab found! Clicking now...")
    driver.execute_script("arguments[0].click();", project_details_tab)
except:
    print("❌ 'Project Details' tab not found or not clickable. Exiting.")
    driver.quit()
    exit()

# ✅ Wait for the Project Details to load
time.sleep(3)

# ✅ Extract Project Address from Table
try:
    print("\n🔍 Searching for 'Project Address' field...")
    project_address_label = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[span[contains(text(), 'Project Address')]]"))
    )

    # ✅ Locate the next sibling <td> containing the actual address
    project_address_value = project_address_label.find_element(By.XPATH, "./following-sibling::td/span")

    # ✅ Extract and clean the address text
    raw_address = project_address_value.get_attribute("innerHTML")
    project_address = raw_address.replace("<br>", ",").strip()

    print(f"🏠 Project Address: {project_address}")


except:
    print("❌ Project Address not found. Exiting.")
    driver.quit()
    exit()

try:
    # ✅ Locate the label for the "Proposed/ Expected Date of Project Completion as specified in Form B"
    completion_date_label = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[span[contains(text(), 'Proposed/ Expected Date of Project Completion as specified in Form B')]]"))
    )

    try:
        # ✅ Locate the next sibling <td> containing the actual date
        completion_date_value = completion_date_label.find_element(By.XPATH, "./following-sibling::td/span")
        
        # ✅ Extract and clean the text
        completion_date = completion_date_value.text.strip()
        print(f"📅 Expected Completion Date: {completion_date}")

    except Exception as e:
        print("⚠️ Could not find the completion date value:", e)

except Exception as e:
    print("⚠️ Could not locate the label for 'Expected Completion Date':", e)

try:
    # ✅ Locate the label for "Total Area of Land Proposed to be developed (in sqr mtrs)"
    land_area_label = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//td[label[contains(text(), 'Total Area of Land Proposed to be developed (in sqr mtrs)')]]"))
    )

    try:
        # ✅ Locate the next sibling <td> containing the actual land area value (no <span> inside)
        land_area_value = land_area_label.find_element(By.XPATH, "./following-sibling::td")

        # ✅ Extract and clean the text
        land_area = land_area_value.text.strip()
        print(f"🏗️ Total Area Proposed: {land_area} sqr mtrs")

    except Exception as e:
        print("⚠️ Could not find the land area value:", e)

except Exception as e:
    print("⚠️ Could not locate the label for 'Total Area of Land Proposed to be developed':", e)



print("\n✅ Process completed successfully!")

# ✅ Keep browser open for debugging
time.sleep(10)  # Give time to view the extracted data before closing
driver.quit()
