import os
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CSV_FILE = "data-portal-query-set.csv"
DOWNLOAD_DIR = os.getcwd()  # Save in the current directory

# Initialize WebDriver
driver = webdriver.Firefox()
driver.get("http://10.10.17.130:11011/login")
driver.maximize_window()

# Login
driver.find_element(By.NAME, "username").send_keys("urvashi.aggarwal@99Acres.com")
driver.find_element(By.NAME, "password").send_keys("Default!157")
driver.find_element(By.XPATH, '//button[text()="SUBMIT"]').click()
time.sleep(2)

updated_rows = []
with open(CSV_FILE, mode="r", newline="") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row)
        if row['flag'].strip().lower() == "true":  # Process only rows where flag is True
            title = row["title"]
            query = row["query"]

            # Navigate to "Add Data Request"
            driver.find_element(By.XPATH, '//a[text()= "Add Data Request"]').click()
            time.sleep(2)

            # Enter data request details
            driver.find_element(By.ID, "title").send_keys(title)
            driver.find_element(By.ID, "type_of_request").click()
            time.sleep(1)

            elem = driver.find_element(By.XPATH, "/html/body/div/form/div[2]/div/ul/li[2]/span")
            time.sleep(1)
            elem.click()

            driver.find_element(By.NAME, "description").send_keys("Download Sys Data")
            
            # Enter query
            query_box = driver.find_element(By.ID, 'query')
            query_box.send_keys(query.strip())

            time.sleep(2)
            driver.find_element(By.NAME, 'submit').click()

            # Wait for request completion and download
            timen = 0
            while timen < 1500:
                if driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[6]/div/div/span').text == 'NONE':
                    time.sleep(10)
                    driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[1]').click()
                elif driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[6]/div/div/span').text == "SUCCEEDED":
                    driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[2]').click()   
                    break
                else:
                    timen += 10
                    time.sleep(5)
                    driver.find_element(By.XPATH, '//*[@id="accuracy_data"]/tbody/tr[1]/td[8]/a[1]').click()
            time.sleep(5)  # Wait for file to appear in download folder

            # Find the latest downloaded CSV file
            files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
            files = sorted(files, key=lambda x: os.path.getctime(os.path.join(DOWNLOAD_DIR, x)), reverse=True)
            if files:
                downloaded_file = os.path.join(DOWNLOAD_DIR, files[0])
                new_file_path = os.path.join(DOWNLOAD_DIR, f"{title}.csv")
                
                print(f"Renaming {downloaded_file} to {new_file_path}")  # Debugging statement
                for _ in range(3):  # Retry up to 3 times
                    try:
                        print("hello")
                        os.rename(downloaded_file, new_file_path)
                        print(f"Renamed {downloaded_file} to {new_file_path}")  # Debugging statement
                        break
                    except PermissionError:
                        print(f"PermissionError: Retrying renaming {downloaded_file} to {new_file_path}")  # Debugging statement
                        time.sleep(1)  # Wait for 1 second before retrying

                # Update row data
                row["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row["flag"] = "false"
                row["folder_path"] = new_file_path

            updated_rows.append(row)

# Write updated data back to CSV
with open(CSV_FILE, mode="w", newline="") as file:
    fieldnames = ["title", "query", "flag", "time", "folder_path"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(updated_rows)

print("Data Download and CSV Updated Successfully!")
driver.quit()