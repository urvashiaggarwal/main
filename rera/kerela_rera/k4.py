from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import time

# Set up Selenium WebDriver
driver = webdriver.Chrome()
driver.get("https://reraonline.kerala.gov.in/SearchList/Search#")

# Click on "Advanced Search"
WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Advance Search"))
).click()

# List to store extracted data
all_data = []

# Get district options (excluding the first one: "Select District")
district_dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'District')))
select = Select(district_dropdown)
district_options = [opt.text.strip() for opt in select.options if opt.text.strip().lower() != "select district"]

# Iterate through each district
for district_name in district_options:
    print(f"Processing district: {district_name}")

    # **Re-locate the dropdown** (Fixes StaleElementReferenceException)
    district_dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'District')))
    select = Select(district_dropdown)
    
    # Select the district
    select.select_by_visible_text(district_name)
    time.sleep(1)  # Give time for UI to update

    # Click Search button
    search_button = driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
    search_button.click()
    time.sleep(3)  # Wait for results to load

    try:
        # Locate table with Project Details
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print(f"Table found for {district_name}")

        # Pagination loop
        while True:
            # Get all rows except header
            rows = table.find_elements(By.TAG_NAME, 'tr')
            print(f"Rows found for {district_name}")

            for row in rows:
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) >= 3:
                    project_name = columns[0].text.strip()
                    promoter_name = columns[1].text.strip()
                    certificate_no = columns[2].text.strip()
                    
                    all_data.append([district_name, project_name, promoter_name, certificate_no])

            # Check if "Next" button is disabled
            try:
                next_page = driver.find_element(By.ID, "btnNext")
                if next_page.get_attribute("disabled"):
                    break  # Exit pagination loop if disabled
                next_page.click()
                time.sleep(2)  # Allow new page to load
            except:
                break  # Exit pagination loop if "Next" button is not found

    except Exception as e:
        print(f"No results for {district_name}: {e}")

# Close the driver
driver.quit()

# Save data to CSV
df = pd.DataFrame(all_data, columns=["District", "Project Name", "Promoter Name", "Certificate No."])
df.to_csv("rera_kerala_projects.csv", index=False)
print("Data saved to rera_kerala_projects.csv")

