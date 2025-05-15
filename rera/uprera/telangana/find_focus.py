
import time
import pandas as pd
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
import fitz  # PyMuPDF
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
driver = webdriver.Chrome()
driver.get("https://rerait.telangana.gov.in/SearchList/Search")

# Wait for the table to load
# WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located(By.XPATH, '//*[@id="gridview"]/div[1]/div/table')
# )
time.sleep(5)
# Initialize a list to store registration numbers
registration_numbers = []

while(True):
# Locate the table
    try:
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        i = 1
    # Iterate over table rows (skip the header row)
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 5:
            # Click the button in the 6th column
                
                view_button = cells[5].find_element(By.TAG_NAME, "a")
                view_button.click()
                time.sleep(5)
            # Switch to the new window/tab
            # driver.switch_to.window(driver.window_handles[1])
            
            # # Wait for the PDF to load
            # time.sleep(10)  # Adjust this sleep time as necessary
            
        
                iframe = driver.find_element(By.XPATH, '//*[@id="divDocumentShowPopUp"]/iframe')
                pdf_url = iframe.get_attribute("src")
                print("PDF URL:", pdf_url)

                


        # Fetch the PDF content
                response = requests.get(pdf_url, stream=True,timeout=15)
                if response.status_code == 200:
                    pdf_document = fitz.open(stream=response.content, filetype="pdf")

            # Extract text from the first page
                    first_page_text = pdf_document[0].get_text()
                    print("Text from First Page:\n", first_page_text)

            # Extract the Registration Number (Modify Regex as needed)
                    import re
                    match = re.search(r'registration\s*number\s*[:\s]+([A-Z]\d{11})', first_page_text,re.IGNORECASE)
                    if match:
                        registration_number = match.group(1)
                        print("Extracted Registration Number:", registration_number)
                    else:
                        print("No registration number found.")
                else:
                    print("Failed to download the PDF.")

                import csv

        # Store the extracted registration number in a CSV file
                with open("registration_numbers.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([registration_number])

                print("Registration number saved successfully!")

                
                # # Close the PDF document
                pdf_document.close()
                
                # Close the current tab and switch back to the main window
                #driver.close()
                # driver.switch_to.window(driver.window_handles[0])
                close_button = driver.find_element(By.XPATH, '//*[@id="pdfDocShowModal"]/div/div/div[1]/button')
                close_button.click()
                time.sleep(2)
                # Optional: Add a delay between iterations
                time.sleep(2)
                i+=1
        # Locate the next page button
            if(i==11):
                try:
                    next_button_xpath = '//*[@id="btnNext"]'
                    next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
                            # Scroll to next button before clicking
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(2)
                            # Click using JavaScript to prevent interception
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Wait for new page to load
    
                    i = 1  # Reset index for new page
                except Exception as e:
                        print(f"Error clicking 'Next' button: {e}")
                        break
    except Exception as e:
        print(f"Error processing row: {e}")
        break
    
    



# Save the registration numbers to a CSV file
# df = pd.DataFrame(registration_numbers, columns=["Registration Number"])
# df.to_csv("registration_numbers.csv", index=False)

# Close the WebDriver
driver.quit()
