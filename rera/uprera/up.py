from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import  os, time
import pandas as pd
import csv
from datetime import date
import json
import glob
 
def download_FP_with_ctrl_s(url, reg_no, cnt):
    base_folder = os.path.abspath("PDFs")
    target_folder = os.path.join(base_folder, reg_no, 'FP')
    target_file = f"FP {cnt}.pdf"
   
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
   
    # Temporary download folder
    download_folder = os.path.abspath("temp_downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
   

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)  
   
    # Simulate Ctrl + S
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
    time.sleep(5)  
    driver.quit()
   
    # Find the most recently downloaded file
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
       
        # Move and rename the file
        new_path = os.path.join(target_folder, target_file)
        os.rename(latest_file, new_path)
        print(f"PDF downloaded and saved as {new_path}")
    else:
        print("No files were downloaded.")
   
    # Clean up the temporary download folder
    if os.path.exists(download_folder):
        os.rmdir(download_folder)
 
def download_OC_with_ctrl_s(url, reg_no):

    base_folder = os.path.abspath("PDFs")
    target_folder = os.path.join(base_folder, reg_no, 'OC')
    target_file = f"OC.pdf"
   
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
   
    # Create a temporary download folder
    download_folder = os.path.abspath("temp_downloads")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
   
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(3)  
   
    # Simulate Ctrl + S
    ActionChains(driver).key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
    time.sleep(5)  
    driver.quit()
   
    # Find the most recently downloaded file
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
       
        # Move and rename the file
        new_path = os.path.join(target_folder, target_file)
        os.rename(latest_file, new_path)
        print(f"PDF downloaded and saved as {new_path}")
    else:
        print("No files were downloaded.")
   
    # Clean up the temporary download folder
    if os.path.exists(download_folder):
        os.rmdir(download_folder)
 
 
def fetch_table_data(driver, table_id):
    """
    Fetch the entire table data once and store it in a list.
   
    :param driver: Selenium WebDriver
    :param table_id: The ID of the table to extract data from
    :return: List of rows (each row is a list of cell values)
    """
    table = driver.find_element(By.ID, table_id)
    rows = table.find_elements(By.TAG_NAME, 'tr')
 
    table_data = []
   
    for row in rows[1:]: 
       
        cells = row.find_elements(By.TAG_NAME, 'td')
        row_data = [cell.text for cell in cells]
        table_data.append(row_data)
   
    return table_data
 
Attempted_date_var = str(date.today())
maindirectory = os.path.abspath(os.getcwd())
HTML = os.path.join(maindirectory, 'OC')
if not os.path.isdir(HTML):
    os.makedirs(HTML)
HTML_PAGE_make_dir = os.path.join(HTML, str(Attempted_date_var))
 
           
if not os.path.isdir(HTML_PAGE_make_dir):
    os.makedirs(HTML_PAGE_make_dir)
chrome_options = webdriver.ChromeOptions()    
settings = {"recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF", "version": 2,"isCssBackgroundEnabled": True,"margins":0  }
prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings),
         "savefile.default_directory": HTML_PAGE_make_dir}
chrome_options.add_experimental_option('prefs', prefs)
 
chrome_options.add_argument('--enable-print-browser')
chrome_options.add_argument('--kiosk-printing')
 
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.up-rera.in/projects")
driver.maximize_window()
cnt = 0
cc="NO"
table_data = fetch_table_data(driver, 'grdPojDetail')
print(table_data)
matching_rows = []
with open("up-focus.csv","r") as csvfile:
    records  = csv.reader(csvfile,delimiter=",")
    next(records)
    for row_1 in records:
        time.sleep(5)
        xid = row_1[0]
        reg_id = xid
        match_found = False
        data = {}
         
 
        for index, row in enumerate(table_data, start=1):  
            formatted_index = f"{index:02}"  
            if len(row) >= 4 and row[3] == reg_id: 
                row_text = row[0]
               
                matching_rows.append((reg_id, formatted_index, row_text)) 
                match_found = True
                x = formatted_index
                match_found = True  
                print(f"Match found for {reg_id} in row {formatted_index}: {row_text}")  
           
                try:
                    print(driver.find_element(By.XPATH, '//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[3]').text)
                    try:
                        data['Registration Number'] = driver.find_element(By.XPATH, '//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[4]').text
                        data['Builder Name'] = driver.find_element(By.XPATH, '//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[2]').text
                        data['Project Category'] = driver.find_element(By.XPATH, '//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[5]').text
                    except:
                        continue
                    data['Project Name'] =driver.find_element(By.XPATH,'//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[3]' ).text
                    data['State'] = 'Uttar Pradesh'
                    data['District'] =driver.find_element(By.XPATH,'//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[6]').text
                    time.sleep(2)
                    try:
                        driver.find_element(By.XPATH, '//*[@id="grdPojDetail"]/tbody/tr['+str(x)+']/td[9]/a').click()
                    except:
                        continue
                    window_after = driver.window_handles[1]
                    driver.switch_to.window(window_after)
                    data['Project Registration Date'] = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_prjregdate').text
                    data['Declared Date Of Completion'] = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_Lblproposedenddt').text
                   
                    data['Tehsil'] =driver.find_element(By.ID,'ctl00_ContentPlaceHolder1_lbltechsil' ).text
                   
                    link = driver.find_element(By.XPATH, '//a[@href="viewprojects"]')
                    ActionChains(driver).move_to_element(link).click().perform()
                   
                    time.sleep(3)
                   
                    driver.switch_to.window(driver.window_handles[2])
                    time.sleep(1)
                    data['Total area in round figure (Sq.mt.)']  = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblTotalArea').get_attribute('value')
                    data['Latitude']  = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblLat1').get_attribute('value')
                    data['Longtitude']  = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblLong1').get_attribute('value')
                    data['Architect Name']  = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblArchName').get_attribute('value')
                    registration_number = data['Registration Number']
 
                    # Locate the table with the specified ID
                    table = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_grvdocumentdetails')
                    print("Documents Table located")
                    # Extract all rows from the table
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    print("Rows extracted")

                    # Loop through the rows and find the floor plan and completion certificate in the first column
                    for row in rows[1:]: 
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        print(cells[1].text)
                        
                        if len(cells) > 1:
                            if cells[1].text == "Floor plans of all types":
                                print("Floor Plan found")
                                download_button = cells[4].find_element(By.TAG_NAME, 'a')
                                download_button.click()
                                print("Download button clicked for Floor Plan")
                                time.sleep(2)
                                download_FP_with_ctrl_s(driver.current_url, registration_number, cnt)
                                cnt += 1
                                break 

                    for row in rows[1:]: 
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) > 1:
                            if cells[1].text == "Proforma of Completion Certificate(Occupancy)":
                                # Click the download button 
                                download_button = cells[4].find_element(By.TAG_NAME, 'a')
                                download_button.click()
                                print("Download button clicked for Completion Certificate")
                                time.sleep(2)
                                download_OC_with_ctrl_s(driver.current_url, registration_number)
                                break  
                    # Locate the table
                    table = driver.find_element(By.ID, 'ShowTableApartment')
                    headers = [header.text for header in table.find_elements(By.TAG_NAME, 'th')]
 
                    print("Length of Headers:", len(headers))
 
                    if len(headers) == 12:
                        csv_file1 = 'apartment_data.csv'
                    else:
                        csv_file1 = 'others_data.csv'
 
                    headers.insert(0, "Registration Number")
                    rows = table.find_elements(By.TAG_NAME, 'tr')
 
                    # Prepare the data
                    data_1 = []
                    for row in rows[1:]:  
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        row_data = [registration_number] + [cell.text for cell in cells]
                        data_1.append(row_data)
 
                    # Save data to CSV
                    file_exists1 = os.path.isfile(csv_file1)
                    with open(csv_file1, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        if not file_exists1: 
                            writer.writerow(headers)
                        writer.writerows(data_1)  
 
                    print(f"Data saved to {csv_file1}")
 
                    df = pd.DataFrame([data])
                    print(data)
 
                # Save to a CSV file
                    csv_file = "up_project_details.csv"
                    file_exists = os.path.isfile(csv_file)
 
                    try:
                        df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
                        print(f"Data has been saved to {csv_file}.")
                    except Exception as file_error:
                        print(f"Error saving CSV: {file_error}")
 
                    #Download the PDF
                    cnt = 1
                    # Find the floor plan text on the page
                    # Locate the table with the specified ID
                    table = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_grvdocumentdetails')
                    print("Documents Table located")
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    print("Rows extracted")
                   
                    # Loop through the rows and find the floor plan 
                    for row in rows[1:]: 
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) > 1 and cells[1].text == "Floor plans of all types":
                            # Click the last column 
                            print("Floor Plan found")
                            download_button = cells[-1].find_element(By.TAG_NAME, 'a')
                            download_button.click()
                            print("Download button clicked for Floor Plan")
                            time.sleep(2)
                            download_FP_with_ctrl_s(driver.current_url, registration_number, cnt)
                            cnt += 1
                            registration_number = data['Registration Number']
                            new_file_name = f"FP/{cnt}{registration_number}.pdf"
                            time.sleep(5)
                            driver.close()
                            driver.switch_to.window(driver.window_handles[2])
                     
                        else:
                            pass
                        if cells > 1 and cells[1].text == "Proforma of Completion Certificate(Occupancy)":
                            print("OC found")
                            try:
                                download_button = cells[-1].find_element(By.TAG_NAME, 'a')
                                if download_button:
                                    download_button.click()
                                    print("Download button clicked for OC")
                                    time.sleep(2)

                                    download_OC_with_ctrl_s(driver.current_url, registration_number)
                                    time.sleep(5)
                                    driver.close()
                                    driver.switch_to.window(driver.window_handles[2])
                            except:
                                continue
                        else:
                            pass
                   
                    print('For Loop Close')
                    driver.close()
                    time.sleep(2)
                    driver.switch_to.window(driver.window_handles[1])
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                except:
                    driver.close()
                    window_after = driver.window_handles[0]
                    driver.switch_to.window(window_after)
                    print('break')
                    continue
           
        time.sleep(3)
 