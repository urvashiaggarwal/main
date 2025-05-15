import time
import pandas as pd
import requests
import fitz  # PyMuPDF
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://rerait.telangana.gov.in/SearchList/Search")

# Wait for the page to load
time.sleep(5)

# Navigate to target page
page_num = 1  # Start from page 1
target_page = 685  # Change this if you need a different page

while page_num < target_page:
    try:
        next_button_xpath = '//*[@id="btnNext"]'
        next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))

        # Scroll to next button before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(2)

        # Click using JavaScript to avoid interception
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(3)  # Wait for new page to load

        page_num += 1
        print(f"Moved to Page {page_num}")

    except Exception as e:
        print(f"Error navigating to page {page_num}: {e}")
        break  # Stop if navigation fails

print("Reached target page, starting extraction...")

# Initialize a list to store registration numbers
registration_numbers = []

# Function to fetch PDF with retry logic
def fetch_pdf_with_retry(pdf_url, retries=3, delay=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for attempt in range(retries):
        try:
            response = requests.get(pdf_url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()  # Raise error for failed responses (4xx, 5xx)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}, retrying {attempt + 1}/{retries}...")
            time.sleep(delay)
    print("Max retries reached. Failed to fetch PDF.")
    return None

while True:
    try:
        # Locate the table
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        i = 1

        # Iterate over table rows (skip header row)
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 5:
                try:
                    # Click the button in the 6th column
                    view_button = cells[5].find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", view_button)  # Use JavaScript click
                    time.sleep(5)  # Wait for modal to open

                    # Locate the iframe containing the PDF
                    iframe = driver.find_element(By.XPATH, '//*[@id="divDocumentShowPopUp"]/iframe')
                    pdf_url = iframe.get_attribute("src")
                    print("PDF URL:", pdf_url)

                    # Fetch the PDF with retry logic
                    response = fetch_pdf_with_retry(pdf_url)
                    if response and response.status_code == 200:
                        pdf_document = fitz.open(stream=response.content, filetype="pdf")

                        # Extract text from the first page
                        first_page_text = pdf_document[0].get_text()
                        print("Text from First Page:\n", first_page_text)

                        # Extract the Registration Number using Regex
                        match = re.search(r'registration\s*number\s*[:\s]+([A-Z]\d{11})', first_page_text, re.IGNORECASE)
                        if match:
                            registration_number = match.group(1)
                            print("Extracted Registration Number:", registration_number)
                        else:
                            print("No registration number found.")
                            registration_number = "N/A"
                    else:
                        print("Failed to download the PDF.")
                        registration_number = "N/A"

                    # Store the extracted registration number in a CSV file
                    with open("registration_numbers.csv", "a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow([registration_number])

                    print("Registration number saved successfully!")

                    # Close the PDF document
                    pdf_document.close()

                    # Close the modal window
                    close_button = driver.find_element(By.XPATH, '//*[@id="pdfDocShowModal"]/div/div/div[1]/button')
                    driver.execute_script("arguments[0].click();", close_button)
                    time.sleep(2)  # Allow time for modal to close
                except Exception as e:
                    print(f"Error processing row: {e}")

                # Optional: Add a delay between row processing to avoid rate limiting
                time.sleep(2)
                i += 1

            # Locate the "Next" button when i == 11 (to move to the next page)
            if i == 11:
                try:
                    next_button_xpath = '//*[@id="btnNext"]'
                    next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))

                    # Scroll to the next button before clicking
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(2)

                    # Click using JavaScript to prevent interception
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Wait for the new page to load

                    i = 1  # Reset index for the new page
                except Exception as e:
                    print(f"Error clicking 'Next' button: {e}")
                    break
    except Exception as e:
        print(f"Unexpected error: {e}")
        break

# Close the WebDriver
driver.quit()
