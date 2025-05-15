from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Selenium WebDriver
driver = webdriver.Chrome()

# Read Registration numbers from CSV
input_csv = 'kerela.csv'  # Your input file
df = pd.read_csv(input_csv)

# Filter only rows where State is Kerala (case insensitive)
df_filtered = df[df['State'].str.lower() == 'kerala']

# Get Registration Numbers as a list
reg_nos = df_filtered['Reg.'].dropna().tolist()



# Open Kerala RERA site
url = "https://rera.kerala.gov.in/explore-projects"
driver.get(url)

# Prepare to collect data
collected_data = []

for reg_no in reg_nos:
    try:
        # Find the search input box
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Project Name / Locality / Promoter / Registration Number"]'))
        )
        
        # Clear and enter registration number
        search_input.clear()
        search_input.send_keys(reg_no)
        time.sleep(1)

        # Click Search button
        search_button = driver.find_element(By.XPATH, '//button[contains(text(), "Search")]')
        driver.execute_script("arguments[0].click();", search_button)

        # Click on "More Info" button if available
        try:
            more_info_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//span[contains(@class, "text-sm") and contains(text(), "More Info")]'))
            )
            driver.execute_script("arguments[0].click();", more_info_button)
            time.sleep(2)  # Wait for the details page to load
        except Exception as e:
            print(f"'More Info' button not found for {reg_no}: {e}")
            continue


        
        # Click on "Complete Project Details" link if available
        try:
            complete_project_details_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Complete Project Details")]'))
            )
            driver.execute_script("arguments[0].click();", complete_project_details_link)
            time.sleep(2)  # Wait for the new window to open

            # Switch to the new window
            # driver.switch_to.window(driver.window_handles[-1])

            # Click on "Construction Progress" tab if available
            try:
                # Wait for the tabs to be present
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//ul[@class="nav nav-tabs"]/li/a'))
                )
                # Locate the tabs using their list structure
                tabs = driver.find_elements(By.XPATH, '//ul[@class="nav nav-tabs"]/li/a')
                for tab in tabs:
                    if "Construction Progress" in tab.get_attribute("textContent"):
                        driver.execute_script("arguments[0].click();", tab)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "construction-progress-content")]'))
                        )  # Wait for the tab content to load
                        break
                else:
                    print(f"'Construction Progress' tab not found for {reg_no}")
            except Exception as e:
                print(f"Error locating 'Construction Progress' tab for {reg_no}: {e}")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue

            # Close the new window and switch back to the main window
            driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"'Complete Project Details' link not found for {reg_no}: {e}")
            continue
        

        # Extract project/building details
                # Wait for Building Details table
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="DivBuilding"]/div/div/div[2]/div/table'))
        )
        
        time.sleep(2)  # Give time for full load

        buildings = []

        # Find the table
        table = driver.find_element(By.XPATH, '//*[@id="DivBuilding"]/div/div/div[2]/div/table')

        # Get all rows except the header
        rows = table.find_elements(By.XPATH, './/tr[position()>1]')
        
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) >= 9:
                building_data = {
                    'RegistrationNumber': reg_no,
                    'BuildingName': cols[1].text.strip(),
                    'ProposedCompletionDate': cols[2].text.strip(),
                    'NumberOfBasements': cols[3].text.strip(),
                    'NumberOfPodiums': cols[4].text.strip(),
                    'NumberOfSlabsOfSuperStructure': cols[5].text.strip(),
                    'NumberOfStilts': cols[6].text.strip(),
                    'NumberOfOpenParking': cols[7].text.strip(),
                    'NumberOfClosedParking': cols[8].text.strip()
                }
                buildings.append(building_data)
        
        # Append buildings to collected_data
        collected_data.extend(buildings)


    except Exception as e:
        print(f"Error processing {reg_no}: {e}")
        driver.get(url)
        time.sleep(2)
        continue

# Close the browser
driver.quit()

# Save to output CSV
output_csv = 'kerala_rera_building_details.csv'
pd.DataFrame(collected_data).to_csv(output_csv, index=False)

print(f"Scraping completed! Data saved to {output_csv}")
