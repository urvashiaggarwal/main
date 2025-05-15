from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Setup Selenium WebDriver
driver = webdriver.Chrome()

# Read Registration numbers from CSV
input_csv = 'kerela.csv'  # Your input file
df = pd.read_csv(input_csv)

# Filter only rows where State is Kerala (case insensitive)
df_filtered = df[df['State'].str.lower() == 'bihar']

# Get Registration Numbers as a list
reg_nos = df_filtered['Reg.'].dropna().tolist()

# Open Bihar RERA site
url = "https://rera.bihar.gov.in/RERASearchPdistrictwise.aspx"
driver.get(url)

# Wait for the dropdown to be present
wait = WebDriverWait(driver, 10)
dropdown = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_ddlCategory")))

# Select "Registration No" from the dropdown
select = Select(dropdown)
select.select_by_visible_text("Registration No")

# Wait for the page to load after selecting the category
time.sleep(5)

# Iterate through the registration numbers and perform the search
for reg_no in reg_nos:
    # Find the input field for registration number
    reg_input = driver.find_element(By.ID, "ContentPlaceHolder1_txtsearch")
    
    # Clear the input field and enter the registration number
    reg_input.clear()
    reg_input.send_keys(reg_no)
    
    # Click the search button
    search_button = driver.find_element(By.ID, "ContentPlaceHolder1_BtnSearch")
    driver.execute_script("arguments[0].click();", search_button)
    
    # Wait for the link to be present in the search results
    try:
        link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'QRCODE.aspx')]")))
        
        # Click the link (assuming it opens in a new window/tab)
        driver.execute_script("arguments[0].click();", link)
        
        # Wait for the new window or tab to open
        original_window = driver.current_window_handle
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        # Wait for the table to be present on the new page
        building_table = wait.until(EC.presence_of_element_located((By.ID, "GV_Building")))

        # Extract rows from the table
        rows = building_table.find_elements(By.TAG_NAME, "tr")
        building_data = []

        # Iterate through table rows and extract data
        for row in rows[1:]:  # Skip header row
            cols = row.find_elements(By.TAG_NAME, "td")
            building_data.append({
                "Reg. No": reg_no,
                "Name of Building": cols[0].text.strip(),
                "Sanctioned No of Floor": cols[1].text.strip(),
                "Type of Apartment": cols[2].text.strip(),
                "No of Apartment": cols[3].text.strip(),
                "Carpet Area": cols[4].text.strip(),
                "Area of Exclusive Balcony": cols[5].text.strip(),
                "Area of Exclusive Open Terrace": cols[6].text.strip()
            })

        # Save data to CSV
        output_csv = "building_details.csv"
        if not os.path.exists(output_csv):
            pd.DataFrame(building_data).to_csv(output_csv, index=False)
        else:
            pd.DataFrame(building_data).to_csv(output_csv, mode='a', header=False, index=False)

    except Exception as e:
        print(f"Error processing registration number {reg_no}: {e}")
        continue

    # Wait for the results to load before moving to the next registration number
    time.sleep(3)

# Close the browser after completing the task
driver.quit()
