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
input_file = 'noida.csv'  # Updated to new input file
output_file = 'housing_floorplan.csv'

# Read input CSV
with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    # Open output CSV in append mode ('a') and write header if needed
    with open(output_file, 'a', newline='', encoding='utf-8') as outcsv:
        writer = csv.writer(outcsv)
        if outcsv.tell() == 0:  # Check if the file is empty
            writer.writerow(['XID','Project','Phase', 'Configuration', 'List Item', 'Price'])  # Write headers only if file is empty

    for row in reader:
        xid = row.get('XID number', '').strip()
        project = row.get('Project Name', '').strip()
        housing_phases = [
            row.get('Housing Phase 1', '').strip(),
            row.get('Housing Phase 2', '').strip(),
            row.get('Housing Phase 3', '').strip(),
            row.get('Housing Phase 4', '').strip()
        ]
        
        for phase_index, link in enumerate(housing_phases, start=1):  # Track phase number
            if not link.startswith('https://housing.com'):
                continue  # Skip invalid or empty URLs
            
            print(f"Processing XID: {xid}, Phase: {phase_index}, Link: {link}")
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

            # Extract floor plan data
            try:
                first_list_container = driver.find_element(By.CLASS_NAME, "config-header-container.css-n0tp0a")
                first_list_items = first_list_container.find_elements(By.TAG_NAME, "li")
                print(f"Found {len(first_list_items)} items in the first list.")

                for item in first_list_items:
                    driver.execute_script("arguments[0].click();", item)
                    time.sleep(1)
                    config_item_text = item.text.strip()
                    print("Clicked an item in the first list.")

                    previous_data = set()
                    while True:
                        try:
                            nested_list_container = driver.find_element(By.CLASS_NAME, "header-container.css-n0tp0a")
                            nested_list_items = nested_list_container.find_elements(By.TAG_NAME, "li")
                            print(f"Found {len(nested_list_items)} items in the nested list.")

                            current_data = set()
                            for sub_item in nested_list_items:
                                list_item_text = sub_item.text.strip()
                                current_data.add(list_item_text)
                                driver.execute_script("arguments[0].click();", sub_item)
                                time.sleep(1)
                                print(f"Clicked an item in the nested list: {list_item_text}")

                                try:
                                    price_element = driver.find_element(By.XPATH, '//*[@id="floorPlan"]/div[2]/div/div/div/div/div/div/div/div[1]/div[1]')
                                    price_text = price_element.text.strip()
                                except:
                                    price_text = "Price not found"

                                with open(output_file, 'a', newline='', encoding='utf-8') as outcsv:
                                    writer = csv.writer(outcsv)
                                    writer.writerow([xid,project, phase_index, config_item_text, list_item_text, price_text])  # Include phase number
                                    outcsv.flush()

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
            
            except Exception as e:
                print(f"Error finding lists: {e}")

print(f"Data extraction complete. Output saved to {output_file}")
driver.quit()
