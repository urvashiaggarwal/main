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

# ✅ Step 1: Enter Registration Number
reg_input = driver.find_element(By.ID, "Input_RegdProject_RERAnumberRegistration")  
reg_input.send_keys("PBRERA-BTI08-PC0292")  # Example registration number

# ✅ Find the CAPTCHA refresh button
refresh_button = driver.find_element(By.CLASS_NAME, "capcha-refresh")

# ✅ Retry CAPTCHA up to 5 times
max_attempts = 5
attempt = 0

while attempt < max_attempts:
    attempt += 1
    print(f"\n🔄 Attempt {attempt} of {max_attempts}")

    # ✅ Step 2: Wait for CAPTCHA to Load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "capcha-badge")))
    captcha_element = driver.find_element(By.CLASS_NAME, "capcha-badge")

    # ✅ Step 3: Take Screenshot of CAPTCHA
    captcha_element.screenshot("captcha.png")
    print("📸 Screenshot taken for CAPTCHA.")

    # ✅ Step 4: Process CAPTCHA Image for OCR
    image = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)  # Convert to grayscale
    _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # Improve clarity
    cv2.imwrite("processed_captcha.png", thresh)  # Save processed image for debugging

    # ✅ Step 5: Extract CAPTCHA Text using OCR
    raw_captcha_text = pytesseract.image_to_string(thresh, config="--psm 6").strip()
    print("🔍 Raw OCR Output:", raw_captcha_text)

    # ✅ Step 6: Ensure CAPTCHA is exactly 6 characters long
    captcha_text = raw_captcha_text.replace(" ", "")  # Remove spaces
    if len(captcha_text) == 6:  
        print("✅ Valid CAPTCHA Extracted:", captcha_text)
    else:
        print("❌ OCR Failed: Extracted CAPTCHA is invalid. Refreshing CAPTCHA...")
        refresh_button.click()  # Click the refresh button
        time.sleep(2)  # Wait for new CAPTCHA to load
        continue  # Retry with new CAPTCHA

    # ✅ Step 7: Enter CAPTCHA Text
    captcha_input = driver.find_element(By.ID, "Input_RegdProject_CaptchaText")
    captcha_input.clear()
    captcha_input.send_keys(captcha_text)

    # ✅ Step 8: Click Search Button
    search_button = driver.find_element(By.ID, "btn_SearchProjectSubmit")
    driver.execute_script("arguments[0].click();", search_button)

    # ✅ Step 9: Wait for response
    time.sleep(5)

    # ✅ Step 10: Check for CAPTCHA failure pop-up
    try:
        pop_up = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "confirm")))
        print("⚠️ Invalid CAPTCHA detected. Clicking OK and retrying...")
        pop_up.click()  # Click "OK" button to retry
        time.sleep(2)  # Short delay before retrying
        refresh_button.click()  # Click refresh to get a new CAPTCHA
        time.sleep(2)  # Wait for new CAPTCHA
    except:
        print("🎉 CAPTCHA Accepted! Proceeding...")
        time.sleep(10)  # Short delay before proceeding
        break  # No pop-up means CAPTCHA was correct

# ✅ Step 11: Close browser after completing the process
print("\n✅ Process completed. Closing browser.")
driver.quit()
