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
logging.info("Starting RERA Rajasthan Scraper...")

# ---------------------- Setup WebDriver ---------------------- #
driver = webdriver.Chrome()  # Ensure ChromeDriver is installed
url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
driver.get(url)

# Wait setup
wait = WebDriverWait(driver, 10)

# Store scraped data
all_data = []

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
    TOTAL_PAGES = 339  # Set manually if needed

# ---------------------- Scrape Each Page ---------------------- #
for page_counter in range(1, TOTAL_PAGES + 1):
    retry_count = 0  # Retry mechanism for stale element issues

    while retry_count < 3:  # Allow up to 3 retries for stale elements
        try:
            logging.info(f"Scraping page {page_counter}/{TOTAL_PAGES}")

            # Wait for table to load
            wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody")))

            # Extract rows dynamically
            rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

            if not rows:
                logging.warning(f"No rows found on page {page_counter}")
                break  # Stop if no rows are found

            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    data = [col.text.strip() for col in cols]

                    if data and len(data) > 1:
                        registration_no = data[5].strip()  # Assuming "Registration No." is the 6th column (index 5)
                        chec_regno = registration_no.replace("/", "_")  # Replace '/' with '_'
                        data.append(chec_regno)  # Add chec_regno column
                        all_data.append(data)
                except StaleElementReferenceException:
                    logging.warning(f"Stale element detected in row on page {page_counter}, retrying row.")
                    continue  # Retry row extraction

            logging.info(f"Scraped {len(rows)} rows from page {page_counter}")

            # Click the next page number dynamically
            if page_counter < TOTAL_PAGES:
                try:
                    page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_counter + 1))))
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

# ---------------------- Save Data to CSV ---------------------- #
driver.quit()
df = pd.DataFrame(
    all_data,
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
df.to_csv("rera_projects.csv", index=False)

logging.info("Data scraping completed successfully and saved to 'rera_rajasthan_projects2.csv'!")
print("Scraping finished! Check 'rera_rajasthan_projects2.csv' and 'rera_scraper.log' for details.")

