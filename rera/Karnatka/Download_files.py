from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import time
import json
import csv

# Folder to store PDFs
download_folder = os.path.join(os.getcwd(), "Downloaded_Certificates")
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# Set up Chrome options for saving PDFs
chrome_options = webdriver.ChromeOptions()
prefs = {
    "savefile.default_directory": download_folder,  
    "printing.print_preview_sticky_settings.appState": json.dumps(
        {
            "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }
    ),
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--kiosk-printing")
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://rera.karnataka.gov.in/viewAllProjects")
driver.maximize_window()

# Read registration numbers from CSV
with open("karnatka_oc.csv", "r") as csvfile:
    records = csv.reader(csvfile, delimiter=",")
    next(records)  

    for row in records:
        registration_id = row[0]
        print(f"Processing: {registration_id}")

        try:
            # Enter registration ID and search
            search_box = driver.find_element(By.ID, 'regNo2')
            search_box.send_keys(Keys.CONTROL, 'a')  # Select existing text
            search_box.send_keys(registration_id)
            driver.find_element(By.NAME, 'btn1').click()
            time.sleep(3)

            # Click on the project link
            try:
                driver.find_element(By.XPATH, "//a[@onclick]").click()
                time.sleep(5)
            except:
                print(f"No project found for {registration_id}. Skipping...")
                continue

            # Click "Completion Details"
            try:
                completion_tab = driver.find_element(By.XPATH, '//*[text()="Completion Details"]')
                completion_tab.click()
                time.sleep(5)
            except:
                print(f"Completion Details not found for {registration_id}. Skipping...")
                driver.back()
                continue

            # Find the "Completion Certificate" text
            try:
                completion_certificate_text = driver.find_element(By.XPATH, '//*[@id="completion"]/div/div[7]/div[3]/div[1]/p')
                print(f"Found completion certificate text for {registration_id}")

                completion_certificate_link = driver.find_element(By.XPATH, '//*[@id="completion"]/div/div[7]/div[3]/div[2]/a')
                completion_certificate_link.click()
                time.sleep(5)

                driver.switch_to.window(driver.window_handles[1])
                time.sleep(3)

                # Save as PDF
                driver.execute_script("window.print();")
                time.sleep(10)

                # Find the latest downloaded file
                files = sorted(os.listdir(download_folder), key=lambda x: os.path.getmtime(os.path.join(download_folder, x)), reverse=True)
                
                if files:
                    print(files)
                    latest_file = files[0]
                    print(latest_file)
                    new_file_name = f"{registration_id}-Completion_Certificate.pdf"
                    print(new_file_name)
                    time.sleep(5) 
                    try:
                        os.rename(os.path.join(download_folder, latest_file), os.path.join(download_folder, new_file_name))
                        print(f"Downloaded: {new_file_name}")
                    except Exception as e:
                        print(f"Error renaming file {latest_file} to {new_file_name}: {e}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"Completion Certificate link not found for {registration_id}. Error: {e}")

            driver.back()
            time.sleep(4)

        except Exception as e:
            print(f"Error processing {registration_id}: {e}")
            driver.back()
            driver.switch_to.window(driver.window_handles[0])
            continue

driver.quit()
print("Process completed.")