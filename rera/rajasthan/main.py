import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

driver = webdriver.Chrome()  
url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
driver.get(url)

wait = WebDriverWait(driver, 10)

csv_filename = "rera_projects.csv"

try:
    # Load existing registration IDs into a set
    existing_df = pd.read_csv(csv_filename)
    existing_ids = set(existing_df["chec_regno"].astype(str).str.strip()) 
except FileNotFoundError:
    existing_ids = set()  

new_data = []

# Ensure Table Loads
try:
    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
except TimeoutException:
    driver.quit()
    exit()

#Scrape Each Page
page_counter = 1
while True:
    retry_count = 0  # Retry mechanism for stale element issues
    while retry_count < 3:  
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
            rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

            if not rows:
                break 

            page_data = []  

            # Extract row data
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                data = [col.text.strip() for col in cols]

                if data and len(data) > 1:
                    page_data.append(data) 

            #Check for New Records
            new_records = []
            for row_data in page_data:
                registration_id = row_data[5].strip()  
                chec_regno = registration_id.replace("/", "_") 

                if chec_regno not in existing_ids:
                    row_data.append(chec_regno)  
                    new_records.append(row_data)  
                    existing_ids.add(chec_regno)  

            if new_records:
                new_data.extend(new_records)  

            #Click Next Page
            try:
                next_page_number = str(page_counter + 1)
                page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, next_page_number)))
                driver.execute_script("arguments[0].click();", page_link)  
                time.sleep(5)  
                page_counter += 1
            except Exception as e:
                print(f"Pagination failed on page {page_counter}.")
                break  

            break 

        except StaleElementReferenceException:
            retry_count += 1
            time.sleep(5)  

            if retry_count >= 3:
                driver.refresh()  
                time.sleep(7)

    if retry_count >= 3:
        break

#Save New Data to CSV 
driver.quit()

if new_data:
    new_df = pd.DataFrame(
        new_data,
        columns=[
            "District Name",
            "Project Name",
            "Project Type",
            "Promoter Name",
            "Application No.",
            "Registration No.",
            "Actions",
            "chec_regno"
        ],
    )

    new_df.to_csv(csv_filename, mode="a", header=False, index=False)

print(f"Scraping finished! {len(new_data)} new records added.")