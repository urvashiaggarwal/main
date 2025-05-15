from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import time
import json
import csv
import shutil
# Folder to store PDFs
download_folder = os.path.join(os.getcwd(), "Downloaded_Certificates")
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# Set up Chrome options for saving PDFs
chrome_options = webdriver.ChromeOptions()
prefs = {
    "savefile.default_directory": download_folder,  # Temp directory
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

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://rera.karnataka.gov.in/viewAllProjects")
driver.maximize_window()


# Read registration numbers from CSV
with open("karnatka_oc.csv", "r") as csvfile:
    records = csv.reader(csvfile, delimiter=",")
    next(records)  # Skip header

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
                print(f"Finding completion certificate text for {registration_id}")
                # Find the completion certificate text element by its text content
                completion_certificate_text = driver.find_element(By.XPATH, '//*[contains(text(), "Completion Certificate")]')
               
                print(completion_certificate_text.text)

                # Find the anchor `<a>` tag next to it
                completion_certificate_link = completion_certificate_text.find_element(By.XPATH, '../../following-sibling::div//a')
                print(completion_certificate_link.get_attribute("href"))
                completion_certificate_link.click()
                time.sleep(5)

                # Switch to new tab
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
                    time.sleep(5)  # Wait for the file to be fully downloaded
                    os.rename(os.path.join(download_folder, latest_file), os.path.join(download_folder, new_file_name))
                    print("hi")
                    #shutil.move(os.path.join(download_folder, latest_file), os.path.join(download_folder, new_file_name))
                    print(f"Downloaded: {new_file_name}")

               

                
                # Close the new tab and switch back
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except:
                print(f"Completion Certificate link not found for {registration_id}.")

            # Go back to search page
            driver.back()
            time.sleep(4)

        except Exception as e:
            print(f"Error processing {registration_id}: {e}")
            driver.back()
            driver.switch_to.window(driver.window_handles[0])
            continue

# Close the driver
driver.quit()
print("Process completed.")

