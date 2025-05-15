import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# ---------------------- Setup WebDriver ---------------------- #
driver = webdriver.Chrome()  # Ensure ChromeDriver is installed
url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
driver.get(url)

# Wait setup
wait = WebDriverWait(driver, 10)

# ---------------------- Load Existing Data ---------------------- #
csv_filename = "rera_projects.csv"

try:
    # Load existing registration IDs into a set
    existing_df = pd.read_csv(csv_filename)
    existing_ids = set(existing_df["chec_regno"].astype(str).str.strip())  # Ensure all IDs are strings and stripped
except FileNotFoundError:
    existing_ids = set()  # No existing file, start fresh

# Store new data
new_data = []

# ---------------------- Ensure Table Loads ---------------------- #
try:
    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
except TimeoutException:
    driver.quit()
    exit()

# ---------------------- Get Total Pages ---------------------- #
try:
    print("Checking for dynamic total pages...")
    last_page = driver.find_element(By.XPATH, "//div[@class='ds4u-ajaxradiolist-field gridPageSize']/preceding-sibling::div//a[last()]/span").text.strip()
    TOTAL_PAGES = int(last_page)  # Extract the last page number dynamically
    print("Found dynamic total pages.")
    print(f"Total Pages: {TOTAL_PAGES}")
except Exception as e:
    TOTAL_PAGES = 343  # Set manually if needed
print(f"Total Pages: {TOTAL_PAGES}")

# ---------------------- Scrape Each Page ---------------------- #
for page_counter in range(1, TOTAL_PAGES + 1):
    retry_count = 0  # Retry mechanism for stale element issues

    while retry_count < 3:  # Allow up to 3 retries for stale elements
        try:
            # Wait for table to load fully
            wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))

            # Re-fetch rows dynamically to handle stale elements
            rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

            if not rows:
                break  # Stop if no rows are found

            page_data = []  # Store all rows on this page

            # Extract row data
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                data = [col.text.strip() for col in cols]

                if data and len(data) > 1:
                    page_data.append(data)  # Collect all rows for this page

            # ---------------------- Check for New Records ---------------------- #
            new_records = []
            for row_data in page_data:
                registration_id = row_data[5].strip()  # Assuming "Registration No." is the 6th column (index 5)
                chec_regno = registration_id.replace("/", "_")  # Replace '/' with '_'

                if chec_regno not in existing_ids:
                    row_data.append(chec_regno)  # Add chec_regno column
                    new_records.append(row_data)  # Store new records
                    existing_ids.add(chec_regno)  # Add new chec_regno to set

            if new_records:
                new_data.extend(new_records)  # Add new records for saving

            # ---------------------- Click Next Page ---------------------- #
            if page_counter < TOTAL_PAGES:
                try:
                    next_page_number = str(page_counter + 1)
                    page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, next_page_number)))
                    driver.execute_script("arguments[0].click();", page_link)  # JavaScript click
                    time.sleep(5)  # Allow time for next page to load
                except Exception as e:
                    break  # Stop if pagination fails

            break  # Exit retry loop if successful

        except StaleElementReferenceException:
            retry_count += 1
            time.sleep(5)  # Small delay before retrying

            if retry_count >= 3:
                driver.refresh()  # Refresh page if retries fail
                time.sleep(7)

# ---------------------- Save New Data to CSV ---------------------- #
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
            "chec_regno",  # New column
        ],
    )

    # Append new records to CSV without overwriting existing data
    new_df.to_csv(csv_filename, mode="a", header=False, index=False)

print(f"Scraping finished! {len(new_data)} new records added.")