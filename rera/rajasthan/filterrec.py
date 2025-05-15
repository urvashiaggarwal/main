import logging
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

# ---------------------- Setup Logging ---------------------- #
logging.basicConfig(
    filename="rera_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Starting RERA Rajasthan Scraper with Duplicate Check...")

# ---------------------- Setup WebDriver ---------------------- #
driver = webdriver.Chrome()  # Ensure ChromeDriver is installed
url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
driver.get(url)

# Wait setup
wait = WebDriverWait(driver, 10)

# ---------------------- Load Existing Data ---------------------- #
csv_filename = "rera_rajasthan_projects2.csv"

try:
    # Load existing registration IDs into a set
    existing_df = pd.read_csv(csv_filename)
    existing_ids = set(existing_df["Registration No."].astype(str))  # Ensure all IDs are strings
    logging.info(f"Loaded {len(existing_ids)} existing records.")
except FileNotFoundError:
    existing_ids = set()  # No existing file, start fresh
    logging.warning("No existing CSV file found. Creating a new one.")

# Store new data
new_data = []

# ---------------------- Ensure Table Loads ---------------------- #
try:
    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
    logging.info("Table loaded successfully.")
except TimeoutException:
    logging.error("Table did not load within timeout. Exiting script.")
    driver.quit()
    exit()

# ---------------------- Get Total Pages ---------------------- #
try:
    last_page = driver.find_element(By.XPATH, "//a[contains(@class,'page-link')][last()]").text.strip()
    TOTAL_PAGES = int(last_page)  # Extract the last page number dynamically
    logging.info(f"Total pages detected: {TOTAL_PAGES}")
except Exception as e:
    logging.error(f"Could not detect total pages: {e}, setting default to 339.")
    TOTAL_PAGES = 340  # Set manually if needed

# ---------------------- Scrape Each Page ---------------------- #
for page_counter in range(1, TOTAL_PAGES + 1):
    retry_count = 0  # Retry mechanism for stale element issues

    while retry_count < 3:  # Allow up to 3 retries for stale elements
        try:
            logging.info(f"Scraping page {page_counter}/{TOTAL_PAGES}")

            # Wait for table to load fully
            wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))

            # Re-fetch rows dynamically to handle stale elements
            rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

            if not rows:
                logging.warning(f"No rows found on page {page_counter}")
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
                registration_id = row_data[5]  # Assuming "Registration No." is the 6th column (index 5)

                if registration_id not in existing_ids:
                    new_records.append(row_data)  # Store new records
                    existing_ids.add(registration_id)  # Add new ID to set

            if new_records:
                new_data.extend(new_records)  # Add new records for saving
                logging.info(f"Found {len(new_records)} new records on page {page_counter}")

            # ---------------------- Click Next Page ---------------------- #
            if page_counter < TOTAL_PAGES:
                try:
                    next_page_number = str(page_counter + 1)
                    page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, next_page_number)))
                    driver.execute_script("arguments[0].click();", page_link)  # JavaScript click
                    time.sleep(5)  # Allow time for next page to load
                except Exception as e:
                    logging.warning(f"Could not click on page {page_counter + 1}: {e}")
                    break  # Stop if pagination fails

            break  # Exit retry loop if successful

        except StaleElementReferenceException:
            logging.error(f"Stale element error on page {page_counter}, retrying attempt {retry_count + 1}...")
            retry_count += 1
            time.sleep(5)  # Small delay before retrying

            if retry_count >= 3:
                logging.error(f"Stale element issue on page {page_counter} after 3 retries, refreshing page...")
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
        ],
    )

    # Append new records to CSV without overwriting existing data
    new_df.to_csv(csv_filename, mode="a", header=False, index=False)
    logging.info(f"Appended {len(new_data)} new records to '{csv_filename}'.")

print(f"Scraping finished! {len(new_data)} new records added.")
