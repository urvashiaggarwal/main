from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import time

# Set up Selenium WebDriver
driver = webdriver.Chrome()  # Ensure chromedriver is in PATH
driver.get("https://reraonline.kerala.gov.in/SearchList/Search#")

# Click on "Advanced Search"
advanced_search = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Advance Search"))
)
advanced_search.click()


# Wait for the District dropdown to load
district_dropdown = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'District'))
)
select = Select(district_dropdown)

# List to store extracted data
all_data = []

# Iterate through each district option
for option in select.options:
    district_name = option.text.strip()

    if district_name.lower() == "select district":  # Skip default option
        continue

    print(f"Processing district: {district_name}")

    # Select the district
    select.select_by_visible_text(district_name)
    time.sleep(1)  # Give time for UI to update

    # Click Search button
    search_button = driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
    search_button.click()

    # Wait for results to load
    time.sleep(3)

    try:
        # Locate table with Project Details
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        print(f"Table found for {district_name}")
        # Get all rows except header
        while True:
            rows = table.find_elements(By.TAG_NAME, 'tr')
            print(f"Rows found for {district_name}")
            for row in rows:
                print(row.text)
                columns = row.find_elements(By.TAG_NAME, "td")
                if len(columns) >= 3:
                    project_name = columns[0].text.strip()
                    promoter_name = columns[1].text.strip()
                    certificate_no = columns[2].text.strip()
                    
                    all_data.append([district_name, project_name, promoter_name, certificate_no])

                # Check if there is a next page
                try:
                    next_page = table.find_element(By.LINK_TEXT, 'Next')
                    if next_page.get_attribute("disabled"):
                        break 
                    next_page.click()
                    time.sleep(2)
                except:
                    break


    except Exception as e:
        print(f"No results for {district_name}: {e}")

# Close the driver
driver.quit()

# Save data to CSV
df = pd.DataFrame(all_data, columns=["District", "Project Name", "Promoter Name", "Certificate No."])
df.to_csv("rera_kerala_projects.csv", index=False)
print("Data saved to rera_kerala_projects.csv")
