import glob
import re
import codecs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import os
import json
from selenium.webdriver.chrome.options import Options
import shutil
import csv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

chrome_options = Options()

# Configure Chrome to save the PDF to the current directory
HTML_PAGE_make_dir = os.path.expanduser("~/Downloads")
chrome_options = webdriver.ChromeOptions() 
settings = {"recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF", "version": 2,"isCssBackgroundEnabled": True,"margins":0  }
prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings),
         "savefile.default_directory": HTML_PAGE_make_dir}
chrome_options.add_experimental_option('prefs', prefs)
chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--kiosk-printing')
 
driver = webdriver.Chrome(options=chrome_options)
url = "https://rera.rajasthan.gov.in/ProjectSearch?Out=Y"
driver.get(url)

# Create folder for storing files if not exists
#os.makedirs("Downloaded_Files", exist_ok=True)

def download_FP_with_ctrl_s(url, textName, reg_no):
    # Define the base directory for storing PDFs
    target_folder = os.path.abspath("Downloaded_Files")
    target_file = f"{clean_filename(textName)} {clean_filename(reg_no)}.pdf"
   
    # Ensure the target folder exists
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
   
    # Create a temporary download folder
    download_folder = os.path.abspath("temp_downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
   
    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
   
    # Set up the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
   
    # Open the URL
    driver.get(url)
    time.sleep(10)  # Increased wait time for the page to load
   
    # Simulate Ctrl + S
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
    time.sleep(10)  # Wait for the download to complete
   
    # Ensure the file is fully downloaded
    download_wait_time = 0
    while not any(fname.endswith('.pdf') for fname in os.listdir(download_folder)) and download_wait_time < 60:
        time.sleep(1)
        download_wait_time += 1
   
    # Close the browser
    driver.quit()
   
    # Find the most recently downloaded file
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    if list_of_files:
        latest_file = max(list_of_files, key=lambda f: os.path.getctime(f))
       
        # Move and rename the file
        new_path = os.path.join(target_folder, target_file)
        os.rename(latest_file, new_path)
        print(f"PDF downloaded and saved as {new_path}")
    else:
        print("No files were downloaded.")
   
    # Clean up the temporary download folder
    if os.path.exists(download_folder):
        os.rmdir(download_folder)
 
# Function to clean file names
def clean_filename(filename):
    return re.sub(r'[\/:*?"<>|]', '_', filename)  # Replace invalid characters with '_'
 
 

# def move_and_rename_last_download(download_dir, new_file_name):
#     """
#     Moves the last downloaded file from the default Downloads folder to a specified directory
#     and renames the file.
   
#     :param download_dir: The target directory to move the file to.
#     :param new_file_name: The new name for the downloaded file.
#     """

#     os.makedirs(download_dir, exist_ok=True)
#     # Path to the default Downloads directory (Change if needed)
#     default_downloads_dir = os.path.expanduser("~/Downloads")
   
#     # List all files in the Downloads folder sorted by modification time (newest first)
#     downloaded_files = sorted(
#         (f for f in os.listdir(default_downloads_dir) if os.path.isfile(os.path.join(default_downloads_dir, f))),
#         key=lambda f: os.path.getmtime(os.path.join(default_downloads_dir, f)),
#         reverse(True)
#     )
   
#     # Ensure there is at least one file
#     if not downloaded_files:
#         print("No files found in the Downloads folder.")
#         return
 
#     # The last downloaded file
#     last_downloaded_file = downloaded_files[0]
#     print(f"Last downloaded file: {last_downloaded_file}")
   
#     # Full path of the last downloaded file
#     source_file_path = os.path.join(default_downloads_dir, last_downloaded_file)
#     print(f"Source file path: {source_file_path}")
   
#     # Check if the file is still downloading (Chrome creates .crdownload files)
#     if last_downloaded_file.endswith(".crdownload"):
#         print("Download still in progress, waiting for completion.")
#         time.sleep(1)
#         return move_and_rename_last_download(download_dir, new_file_name)  # Recurse to check again
   
#     # Target path in the desired directory with the new name
#     target_file_path = os.path.join(download_dir, new_file_name)
#     print(f"Target file path: {target_file_path}")
   
#     # Move and rename the file
#     try:
#         print(f"Moving and renaming file to {target_file_path}...")
#         shutil.move(source_file_path, target_file_path)
#         print(f"File moved and renamed successfully.")
#         print(f"Moved and renamed file to {target_file_path}")
#     except Exception as e:
#         print(f"Error while moving or renaming the file: {e}")
 

# Read registration numbers from CSV file with specified encoding
focus_list_df = pd.read_csv('rj-focus-list.csv', encoding='ISO-8859-1')
registration_numbers = focus_list_df['Registration No'].apply(lambda x: x.split(' ')[0]).tolist()

# Initialize variables
table_data = []
amenities_data = []

headers = ["District Name","Project Name","Project Type",
                "Promoter Name","Application No.","Registration No", "Tehsil","Street/ Locality",
           "Open Area (In sq. meters)", "Total Area Of Project (In sq. meters)", "Sanctioned Number Of Apartments / Plots"]
amenities_headers = ["Registration No", "Common Area And Facilities,Amenities", "Proposed", "Percentage Of Completion"]

# Loop through each registration number
for index, registration_no in enumerate(registration_numbers):
    try:
        # Enter registration number in the search field
        search_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="certificateNo"]'))
        )
        search_field.clear()
        search_field.send_keys(registration_no)

        # Click the search button
        search_button = driver.find_element(By.XPATH, '//*[@id="btn_SearchProjectSubmit"]')
        if index == 0:
            search_button.click()
            time.sleep(2)
        search_button.click()
        print(f"Search button clicked for {registration_no}.")
        time.sleep(15)  # Increased sleep time to allow the page to load

        registration_no =  registration_no.replace("/","-")

        # Extract data for the registration number
        try:
            columns = driver.find_elements(By.XPATH, '//td')
            if len(columns) > 0:
                row_data = [col.text.strip() for col in columns[:-1]]
                table_data.append(row_data)

                # Click "Project Details" button
                details_button = columns[-1].find_element(By.TAG_NAME, 'a')
                details_button.click()
                time.sleep(3)

                # Switch to new tab
                driver.switch_to.window(driver.window_handles[1])
                # Extract "Updated project details as on " and click link
                try:
                    updated_details_element = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Updated project details as on')]/following-sibling::td/a"))
                    )
                    updated_details_url = updated_details_element.get_attribute("href")
                    updated_details_element.click()
                    time.sleep(5)

                    # Switch to new tab
                    driver.switch_to.window(driver.window_handles[2])

                    # Extract tehsil from new window
                    try:
                        tehsil_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Tehsil')]/following-sibling::td"))
                        )
                        tehsil_text = tehsil_element.text.strip()
                        row_data.append(tehsil_text)
                        print(f"Tehsil: {tehsil_text}")
                    except Exception as e:
                        print(f"Tehsil not found for {registration_no}: {e}")
                        row_data.append("N/A")

                    # Extract Street/Locality from new window
                    try:
                        street_locality_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Street/ Locality')]/following-sibling::td"))
                        )
                        street_locality_text = street_locality_element.text.strip()
                        row_data.append(street_locality_text)
                        print(f"Street/ Locality: {street_locality_text}")
                    except Exception as e:
                        print(f"Street/ Locality not found for {registration_no}: {e}")
                        row_data.append("N/A")

                    # Extract Open Area (In sq. meters)
                    try:
                        open_area_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Open Area(In sq. meters)')]/following-sibling::td"))
                        )
                        open_area_text = open_area_element.text.strip()
                        row_data.append(open_area_text)
                        print(f"Open Area (In sq. meters): {open_area_text}")
                    except Exception as e:
                        print(f"Open Area (In sq. meters) not found for {registration_no}: {e}")
                        row_data.append("N/A")

                    # Extract Total Area Of Project (In sq. meters)
                    try:
                        total_area_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Total Area Of Project (In sq. meters)')]/following-sibling::td"))
                        )
                        total_area_text = total_area_element.text.strip()
                        row_data.append(total_area_text)
                        print(f"Total Area Of Project (In sq. meters): {total_area_text}")
                    except Exception as e:
                        print(f"Total Area Of Project (In sq. meters) not found for {registration_no}: {e}")
                        row_data.append("N/A")

                    # Extract Sanctioned Number Of Apartments / Plots
                    try:
                        sanctioned_apartments_element = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Sanctioned Number Of Apartments / Plots')]/following-sibling::td"))
                        )
                        sanctioned_apartments_text = sanctioned_apartments_element.text.strip()
                        row_data.append(sanctioned_apartments_text)
                        print(f"Sanctioned Number Of Apartments / Plots: {sanctioned_apartments_text}")
                    except Exception as e:
                        print(f"Sanctioned Number Of Apartments / Plots not found for {registration_no}: {e}")
                        row_data.append("N/A")

                    # Extract amenities data
                    try:
                        # Locate the table containing amenities data
                        amenities_table = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.XPATH, "//table[contains(., 'Common Area And Facilities')]"))
                        )
                        # Iterate through each row in the table
                        rows = amenities_table.find_elements(By.XPATH, ".//tr")
                        for row in rows[1:]:  # Skip the header row
                            cells = row.find_elements(By.XPATH, ".//td")
                            if len(cells) >= 4:
                                common_area = cells[0].text.strip()
                               # amenities = cells[1].text.strip()
                                proposed = cells[1].text.strip()
                                completion = cells[2].text.strip()
                    
                                amenities_data.append([ registration_no,common_area, proposed, completion])
                                print(f"Registration No: {registration_no},Common Area and Facilities,Amenities: {common_area}, Proposed: {proposed}, Percentage of Completion: {completion}")
                    except Exception as e:
                        print(f"Amenities data not found for {registration_no}: {e}")
                        amenities_data.append([registration_no, "N/A", "N/A", "N/A", "N/A"])
                        # Check if amenities CSV file exists, if not create it with headers
                    # amenities_output_file = 'rajasthan-amenities-data.csv'
                    # if not os.path.isfile(amenities_output_file):
                    #     with open(amenities_output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    #         writer = csv.writer(csvfile)
                    #         writer.writerow(amenities_headers)
                    #         writer.writerows(amenities_data)
                                                    
                    amenities_output_file = 'rajasthan-amenities-data.csv'
                    amenities_file_exists = os.path.isfile(amenities_output_file)

                    with open(amenities_output_file, 'a', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        if csvfile.tell() == 0:
                            writer.writerow(amenities_headers)  # Write headers if file is empty
                        writer.writerows(amenities_data)

                    # Close tab and switch back
                    driver.close()
                    driver.switch_to.window(driver.window_handles[1])
                except Exception as e:
                    print(f"Updated project details as on not found for {registration_no}: {e}")
                    row_data.append("N/A")
                # Extract & Download Occupancy Certificate
                try:
                    occupancy_certificate_link = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Occupancy Certificate')]/following-sibling::td/a"))
                    )
                    cert_url = occupancy_certificate_link.get_attribute("href")
                    download_FP_with_ctrl_s(cert_url, "Occupancy_Certificate", registration_no)
                except Exception as e:
                    print(f"Occupancy Certificate not found for {registration_no}: {e}")

                # Extract & Download Approved Maps
                try:
                    approved_maps_link = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Approved maps as at the time of registration')]/following-sibling::td/a"))
                    )
                    map_url = approved_maps_link.get_attribute("href")
                    download_FP_with_ctrl_s(map_url, "Approved_Map", registration_no)
                except Exception as e:
                    print(f"Approved Map not found for {registration_no}: {e}")

                # Extract & Download "Registration Valid Upto" Document
                try:
                    valid_upto_element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Registration Valid upto')]/following-sibling::td/a"))
                    )
                    valid_upto_url = valid_upto_element.get_attribute("href")
                    download_FP_with_ctrl_s(valid_upto_url, "Registration_Valid_Upto", registration_no)
                except Exception as e:
                    print(f"Registration Valid Upto document not found for {registration_no}: {e}")

                # Close tab and switch back
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        except Exception as e:
            print(f"Error extracting data for registration number {registration_no}: {e}")
            continue  # Move to the next row even if one fails

    except Exception as e:
        print(f"Unexpected error for registration number {registration_no}: {e}")
        continue  # Continue to the next registration number even if one fails



# Save extracted data to CSV without using DataFrame
output_file = 'rajasthan-registration-data.csv'
file_exists = os.path.isfile(output_file)

with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    if csvfile.tell() == 0:
        writer.writerow(headers)  # Write headers if file is empty
    writer.writerows(table_data)

# Save amenities data to CSV
# amenities_output_file = 'rajasthan-amenities-data.csv'
# amenities_file_exists = os.path.isfile(amenities_output_file)

# with open(amenities_output_file, 'a', newline='', encoding='utf-8') as csvfile:
#     writer = csv.writer(csvfile)
#     if csvfile.tell() == 0:
#         writer.writerow(amenities_headers)  # Write headers if file is empty
#     writer.writerows(amenities_data)

print("Scraping completed successfully.")
driver.quit()
