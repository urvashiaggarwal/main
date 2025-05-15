from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import time
import csv

# Set up Selenium WebDriver
driver = webdriver.Chrome()  # Ensure chromedriver is in PATH
driver.get("https://reraonline.kerala.gov.in/SearchList/Search#")

# Open CSV file for writing
with open("rera_kerala_new_final.csv", mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["District", "Project Name", "Promoter Name", "Certificate No."])

    # List to store extracted data
    all_data = []
    vis = set()

    # Click on "Advanced Search"
    advanced_search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.LINK_TEXT, "Advance Search"))
    )
    advanced_search.click()

    # Wait for the District dropdown to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'District'))
    )

    # Iterate through each district option
    while True:
        # Reinitialize Select object inside loop
        district_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'District'))
        )
        select = Select(district_dropdown)

        district_options = [option.text.strip() for option in select.options if option.text.strip().lower() != "select district"]

        if not district_options:
            break  # Exit if no districts found

        for district_name in district_options:
            if district_name in vis:
                driver.quit()
                break

            print(f"Processing district: {district_name}")
            time.sleep(5)
            # Select the district
            select.select_by_visible_text(district_name)
            time.sleep(5)  # Allow UI to update

            # Click Search button
            search_button = driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
            search_button.click()

            # Wait for results to load
            time.sleep(5)

            try:
                # Locate table with Project Details
                table = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'table'))
                )
                print(f"Table found for {district_name}")

                # Pagination loop
                while True:
                    # Re-fetch the table in every loop to avoid stale elements
                    table = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'table'))
                    )
                    rows = table.find_elements(By.TAG_NAME, 'tr')

                    for row in rows:
                        columns = row.find_elements(By.TAG_NAME, "td")
                        if len(columns) >= 3:
                            project_name = columns[0].text.strip()
                            promoter_name = columns[1].text.strip()
                            certificate_no = columns[2].text.strip()

                            # Write data to CSV file
                            writer.writerow([district_name, project_name, promoter_name, certificate_no])

                    # Check if there is a next page **after processing all rows**
                    try:
                        next_page = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="btnNext"]'))
                        )
                        if next_page.get_attribute("disabled"):
                            break  # Exit pagination loop if disabled
                        print("Next page found")
                        driver.execute_script("arguments[0].click();", next_page)
                        time.sleep(5)  # Allow new page to load
                    except:
                        break  # Exit pagination loop if "Next" button is not found
                vis.add(district_name)

            except Exception as e:
                print(f"No results for {district_name}: {e}")

            # Click "Advanced Search" again to reset the page before selecting the next district
            advanced_search = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Advance Search"))
            )
            advanced_search.click()
            time.sleep(5)  # Allow UI to update
            district_dropdown = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'District'))
            )
            select = Select(district_dropdown)

# Close the driver
driver.quit()

print("Data saved to rera_kerala_new_final.csv")