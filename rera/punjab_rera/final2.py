import time
import csv
import cv2
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException

# Set up Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\urvashi.aggarwal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Read Registration Numbers from CSV
input_csv = "input.csv"  # Replace with your CSV filename
output_csv = "output2.csv"

with open(input_csv, "r") as file:
    reader = csv.reader(file)
    registration_numbers = [row[0] for row in reader]  # Assuming single column CSV

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://rera.punjab.gov.in/reraindex/publicview/projectinfo")

# Function to solve CAPTCHA
def solve_captcha():
    for attempt in range(5):  # Retry up to 5 times
        try:
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "capcha-badge"))
            )
            captcha_element.screenshot("captcha.png")

            image = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)
            _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            captcha_text = pytesseract.image_to_string(thresh, config="--psm 6").strip()
            if len(captcha_text) == 6:
                return captcha_text

            driver.find_element(By.CLASS_NAME, "capcha-refresh").click()
            time.sleep(2)

        except Exception:
            pass

    driver.quit()
    exit()

# Function to handle invalid CAPTCHA popup
def handle_invalid_captcha_popup():
    try:
        popup_ok_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "swal2-confirm"))
        )
        popup_ok_button.click()
        time.sleep(2)
    except TimeoutException:
        pass

# Process Each Registration Number
data = []
for reg_no in registration_numbers:
    try:
        reg_input = driver.find_element(By.ID, "Input_RegdProject_RERAnumberRegistration")
        reg_input.clear()
        reg_input.send_keys(reg_no)

        for attempt in range(5):  # Retry CAPTCHA 5 times if needed
            captcha_text = solve_captcha()
            captcha_input = driver.find_element(By.ID, "Input_RegdProject_CaptchaText")
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)

            search_button = driver.find_element(By.ID, "btn_SearchProjectSubmit")
            driver.execute_script("arguments[0].click();", search_button)

            time.sleep(5)

            # Check if invalid CAPTCHA pop-up appears
            handle_invalid_captcha_popup()

            # If CAPTCHA is correct, break out of retry loop
            if "invalid captcha" not in driver.page_source.lower():
                break

        try:
            notification = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-pnotify-container"))
            )
            driver.execute_script("arguments[0].remove();", notification)
        except:
            pass

        try:
            view_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "modalOpenerButtonRegdProject"))
            )
            driver.execute_script("arguments[0].click();", view_button)
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", view_button)
        except Exception:
            continue

        try:
            project_details_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@data-toggle='tab' and @href='#Projects']"))
            )
            driver.execute_script("arguments[0].click();", project_details_tab)
        except:
            continue

        try:
            project_address_label = driver.find_element(By.XPATH, "//td[span[contains(text(), 'Project Address')]]")
            project_address_value = project_address_label.find_element(By.XPATH, "following-sibling::td/span").get_attribute("innerHTML")
            project_address = " ".join(project_address_value.split("<br>")).strip()
        except:
            project_address = "N/A"

        try:
            total_area_label = driver.find_element(By.XPATH, "//td[label[contains(text(), 'Total Area of Land Proposed to be developed')]]")
            total_area = total_area_label.find_element(By.XPATH, "following-sibling::td").text.strip()
        except:
            total_area = "N/A"

        try:
            completion_date_label = driver.find_element(By.XPATH, "//td[span[contains(text(), 'Proposed/ Expected Date of Project Completion')]]")
            completion_date = completion_date_label.find_element(By.XPATH, "following-sibling::td/span").get_attribute("innerHTML")
            completion_date = " ".join(completion_date.split("<br>")).strip()
        except:
            completion_date = "N/A"

        data.append([reg_no, project_address, total_area, completion_date])

    except Exception:
        continue

# Write Data to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Registration No", "Project Address", "Total Area", "Completion Date"])
    writer.writerows(data)

driver.quit()
