import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to setup Chrome driver: {str(e)}")
        raise


def scrape_table(url):
    logging.info("Starting to scrape URL: %s", url)
    driver = None

    try:
        driver = setup_driver()
        logging.info("Chrome driver setup successful")

        # Load the page
        driver.get(url)
        logging.info("Successfully loaded the page")

        # Wait for the table to be present
        wait = WebDriverWait(driver, 20)
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#OuterProjectGrid")))
        logging.info("Table element found")

        # Give extra time for the table to fully load
        time.sleep(5)

        # Try multiple selectors for headers
        header_selectors = [
            "#OuterProjectGrid .ds4u-header .ds4u-hrow span",
            "#OuterProjectGrid thead tr td",
            "#OuterProjectGrid .ds4u-header tr td",
            "#OuterProjectGrid th"
        ]

        headers = []
        for selector in header_selectors:
            header_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            headers = [header.text.strip() for header in header_elements if header.text.strip()]
            if headers:
                logging.info(f"Found headers using selector '{selector}': {headers}")
                break

        if not headers:
            logging.error("Could not find header elements with any selector")
            # Save page source for debugging
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logging.info("Saved page source to debug_page_source.html")
            return

        # Find all data rows
        rows = driver.find_elements(By.CSS_SELECTOR, "#OuterProjectGrid tbody tr")
        logging.info(f"Found {len(rows)} data rows")

        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.strip() for cell in cells]
            if any(row_data):  # Only add non-empty rows
                data.append(row_data)

        if data:
            # Ensure data and headers match in length
            max_length = max(len(headers), max(len(row) for row in data))
            headers = headers + ['Column_' + str(i) for i in range(len(headers), max_length)]

            df = pd.DataFrame(data, columns=headers)
            logging.info(f"DataFrame created with {df.shape[0]} rows and {df.shape[1]} columns")

            # Remove any empty columns
            df = df.dropna(axis=1, how='all')

            csv_filename = "rera_data.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            logging.info(f"Data saved to {csv_filename}")

            # Print first few rows for verification
            logging.info("\nFirst few rows of extracted data:")
            logging.info(df.head().to_string())
        else:
            logging.warning("No data rows were extracted!")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        if driver:
            # Save screenshot and page source for debugging
            driver.save_screenshot("error_screenshot.png")
            with open('error_page_source.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logging.info("Saved error screenshot and page source for debugging")

  '''  finally:
        if driver:
            driver.quit()
'''

if __name__ == "__main__":
    url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
    scrape_table(url)