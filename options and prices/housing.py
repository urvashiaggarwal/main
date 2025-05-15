

import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# Set up Selenium WebDriver
options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# File names
input_file = 'new21.csv'
output_file = 'housing_21.csv'

# Read input CSV
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    # Open output CSV in append mode ('a') and write header if needed
    with open(output_file, 'a', newline='', encoding='utf-8') as outcsv:
        writer = csv.writer(outcsv)
        if outcsv.tell() == 0:  # Check if the file is empty
            writer.writerow(['XID', 'Floor Plan'])  # Write headers only if file is empty

    for row in reader:
        xid = row.get('Index', '').strip()
        link = row.get('Comp 2', '').strip()

        print("Processing XID:", xid, "Link:", link)

        if link.startswith('https://housing.com'):
            driver.get(link)
            time.sleep(2)  # Wait for the page to settle

            # Click the 'Ok, Got it' button if it appears
            try:
                ok_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="innerApp"]/div[2]/div[1]/div[1]/div/button'))
                )
                driver.execute_script("arguments[0].click();", ok_button)
                print("Clicked 'Ok, Got it' button.")
            except:
                print("No 'Ok, Got it' button found or already dismissed.")

            # Wait for page load
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                print(f"Page load timeout for {link}")
                continue  # Skip this entry

            extracted_data = []  # Store extracted data
            floor_plans=[]
            # Find all containers with class "config-header-container css-n0tp0a"
            try:
                first_list_container = driver.find_element(By.CLASS_NAME, "config-header-container.css-n0tp0a")  # The first one is the main list
                first_list_items = first_list_container.find_elements(By.TAG_NAME, "li")
                print(f"Found {len(first_list_items)} items in the first list.")

                for item in first_list_items:
                    driver.execute_script("arguments[0].click();", item)  # Click via JavaScript
                    time.sleep(1)
                    config_item = item.text.strip().split("\n")[0]  # Extract only the configuration (e.g., "4 BHK Apartment")
                    print(f"Clicked an item in the first list: {config_item}")

                    previous_data = set()
                    while True:
                        # Look for a nested list inside THIS item (not globally)
                        try:
                            nested_list_container = driver.find_element(By.CLASS_NAME, "header-container.css-n0tp0a")
                            nested_list_items = nested_list_container.find_elements(By.TAG_NAME, "li")
                            print(f"Found {len(nested_list_items)} items in the nested list.")

                            current_data = set()
                            for sub_item in nested_list_items:
                                list_item_text = sub_item.text.strip()  # Get the text of the sub-item
                                current_data.add(list_item_text)
                                driver.execute_script("arguments[0].click();", sub_item)  # Click via JavaScript
                                time.sleep(1)
                                print(f"Clicked an item in the nested list: {list_item_text}")

                                # Extract price from the given XPath
                                try:
                                    price_element = driver.find_element(By.XPATH, '//*[@id="floorPlan"]/div[2]/div/div/div/div/div/div/div/div[1]/div[1]')
                                    price_text = price_element.text.strip()
                                except:
                                    
                                    price_text = "N/A"

                                # Click on the button specified by the given XPath
                                try:
                                    button_element = driver.find_element(By.XPATH, '//*[@id="floorPlan"]/div[2]/div/div/div/div/div/div/div/div[1]/div[2]/div/span[2]')
                                    driver.execute_script("arguments[0].click();", button_element)
                                    time.sleep(1)
                                    print("Clicked on the specified button.")
                                except:
                                    print("Button not found or could not be clicked.")

                                # Extract Super Builtup Area from the given class
                                try:
                                    area_element = driver.find_element(By.XPATH, '//*[@id="floorPlan"]/div[2]/div/div/div/div/div/div/div/div[3]/div[1]/div[2]/div[1]')
                                    area_text = area_element.text.strip()
                                except:
                                    area_text = "N/A"

                                floor_plan_details = f"{config_item}- {area_text}-{list_item_text} - {price_text} "
                                print(f"Floor Plan Details: {floor_plan_details}")
                                floor_plans.append(floor_plan_details)

                                
                            if current_data == previous_data:
                                print("No new data found. Ending pagination.")
                                break
                            previous_data = current_data

                        
                        
                        except StaleElementReferenceException:
                            print("Stale element encountered. Retrying...")
                            continue
                        except:
                            print("No nested list found under this item.")
                            break

                    with open(output_file, 'a', newline='', encoding='utf-8') as outcsv:
                        writer = csv.writer(outcsv)
                        writer.writerow([xid, floor_plans])  # Write the last floor plan details
                        outcsv.flush()  # Ensure data is written immediately

                        
                        # Check for the Next button
                        try:
                            next_button = driver.find_element(By.XPATH, '//*[@id="floorPlan"]/div[2]/div/div/div/div[1]/div[2]')
                            next_button_class = next_button.get_attribute("class")
                            if "css-hskvoc" in next_button_class:
                                print("Next button is disabled. Ending pagination.")
                                break
                            driver.execute_script("arguments[0].click();", next_button)
                            time.sleep(2)
                            print("Clicked 'Next' button.")
                        except:
                            print("No 'Next' button found or page did not change. Ending pagination.")
                            break

                        #  Append row immediately to CSV
                        
            
            except Exception as e:
                print(f"Error finding lists: {e}")

print(f"Data extraction complete. Output saved to {output_file}")
driver.quit()
