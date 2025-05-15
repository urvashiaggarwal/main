import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
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
        return None

def scrape_table(driver, url):
    try:
        driver.get(url)
        time.sleep(3)  # Wait for the page to load

        all_data = []
        while True:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.select_one('#OuterProjectGrid')

            if table:
                rows = table.find_all('tr')
                logging.info("Rows extracted: %d", len(rows))

                # Extract headers
                if not all_data:
                    headers = [header.text.strip() for header in rows[0].find_all('th')[:-1]]  # Exclude last column header
                    logging.info("Headers: %s", headers)

                # Extract rows
                for row in rows[1:]:
                    cols = row.find_all('td')[:-1]  # Exclude last column data
                    cols = [col.text.strip() for col in cols]
                    all_data.append(cols)

                logging.info("Data extracted from current page")

                # Check if there is a next page button and click it
                try:
                    next_button = driver.find_element(By.XPATH, '//*[@id="OuterProjectGrid"]/div[4]/div[4]/button[2]')
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)  # Wait for the next page to load
                    else:
                        break
                except Exception as e:
                    logging.warning("No next button found or an error occurred: %s", str(e))
                    break
            else:
                logging.warning("No table found with the given selector")
                break

        # Create DataFrame
        if all_data:
            df = pd.DataFrame(all_data, columns=headers)
            logging.info("DataFrame:\n%s", df.head().to_string())

            # Save DataFrame to CSV
            df.to_csv('output2.csv', index=False)
            logging.info("Data saved to output.csv")
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

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
    driver = setup_driver()
    if driver:
        scrape_table(driver, url)